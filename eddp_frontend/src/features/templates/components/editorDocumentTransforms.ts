type PMMark = Record<string, unknown>;

export type PMNode = {
  type: string;
  attrs?: Record<string, unknown>;
  content?: PMNode[];
  text?: string;
  marks?: PMMark[];
};

export type PMDoc = {
  type: 'doc';
  content: PMNode[];
} & Record<string, unknown>;

export type PageSize = 'A4' | 'A3' | 'LETTER' | 'LEGAL';
export type Orientation = 'PORTRAIT' | 'LANDSCAPE';

export type LayoutMargins = {
  top?: number;
  bottom?: number;
  left?: number;
  right?: number;
};

export type PaginationConfig = {
  pageSize: PageSize;
  orientation: Orientation;
  marginPx: number;
};

const PAGE_DIMENSIONS: Record<PageSize, { width: number; height: number }> = {
  A4: { width: 794, height: 1123 },
  A3: { width: 1123, height: 1587 },
  LETTER: { width: 816, height: 1056 },
  LEGAL: { width: 816, height: 1344 },
};

const PLACEHOLDER_PATTERN = /<\s*([A-Za-z][A-Za-z0-9_]*)\s*>|\{\{\s*([A-Za-z][A-Za-z0-9_]*)\s*\}\}|\{\s*([A-Za-z][A-Za-z0-9_]*)\s*\}/g;

const DYNAMIC_TABLE_TOKENS = new Set([
  'ADDRESS_TABLE',
  'SIGNATURE_TABLE',
  'AMORTIZATION_TABLE',
  'PAYMENT_SCHEDULE',
  'CO_APPLICANT_TABLE',
]);

const SIGNATURE_TOKENS = new Set([
  'SIGNATURE',
  'AUTHORIZED_SIGNATORY',
  'CO_APPLICANT_SIGNATURE',
  'SIGNATURE_TABLE',
]);

const IMAGE_TOKENS = new Set([
  'CUSTOMER_PHOTO',
  'PROPERTY_IMAGE',
  'QR_CODE',
  'COMPANY_LOGO',
]);

const normalizeToken = (raw: string): string =>
  raw
    .trim()
    .toUpperCase()
    .replace(/[^A-Z0-9_]+/g, '_')
    .replace(/_+/g, '_')
    .replace(/^_+|_+$/g, '');

const mapVariableNodeType = (token: string): PMNode['type'] => {
  if (IMAGE_TOKENS.has(token) || token.endsWith('_IMAGE') || token.endsWith('_PHOTO')) {
    return 'imagePlaceholderVariable';
  }
  if (DYNAMIC_TABLE_TOKENS.has(token) || token.endsWith('_TABLE') || token.endsWith('_SCHEDULE')) {
    return 'dynamicTableVariable';
  }
  if (SIGNATURE_TOKENS.has(token) || token.includes('SIGNATURE')) {
    return 'signatureVariable';
  }
  return 'variableChip';
};

const buildTableNode = (rows: Array<Array<string>>): PMNode => ({
  type: 'table',
  content: rows.map((row, rowIndex) => ({
    type: 'tableRow',
    content: row.map((value) => ({
      type: rowIndex === 0 ? 'tableHeader' : 'tableCell',
      content: [
        {
          type: 'paragraph',
          content: [{ type: 'text', text: value }],
        },
      ],
    })),
  })),
});

const DYNAMIC_TABLE_BY_TOKEN: Record<string, PMNode> = {
  ADDRESS_TABLE: buildTableNode([
    ['Address Line 1', 'Address Line 2', 'City', 'Postal Code'],
    ['<ADDRESS_LINE_1>', '<ADDRESS_LINE_2>', '<CITY>', '<POSTAL_CODE>'],
  ]),
  SIGNATURE_TABLE: buildTableNode([
    ['Name', 'Signature', 'Date'],
    ['<SIGNATORY_NAME>', '<SIGNATURE>', '<SIGNATURE_DATE>'],
  ]),
  AMORTIZATION_TABLE: buildTableNode([
    ['Installment', 'Principal', 'Interest', 'Balance'],
    ['<EMI_NO>', '<PRINCIPAL_COMPONENT>', '<INTEREST_COMPONENT>', '<OUTSTANDING_BALANCE>'],
  ]),
  PAYMENT_SCHEDULE: buildTableNode([
    ['Due Date', 'Amount', 'Status'],
    ['<DUE_DATE>', '<INSTALLMENT_AMOUNT>', '<PAYMENT_STATUS>'],
  ]),
  CUSTOMER_TABLE: buildTableNode([
    ['Customer ID', 'Customer Name', 'Contact'],
    ['<CUSTOMER_ID>', '<CUSTOMER_NAME>', '<CUSTOMER_CONTACT>'],
  ]),
};

const isTextNode = (node: PMNode): boolean => node.type === 'text' && typeof node.text === 'string';

const splitTextNodeToVariableNodes = (node: PMNode): PMNode[] => {
  if (!isTextNode(node)) {
    return [node];
  }

  const text = node.text || '';
  if (!text) {
    return [node];
  }

  const nodes: PMNode[] = [];
  let cursor = 0;

  for (const match of text.matchAll(PLACEHOLDER_PATTERN)) {
    const index = match.index ?? 0;
    if (index > cursor) {
      nodes.push({
        type: 'text',
        text: text.slice(cursor, index),
        marks: node.marks,
      });
    }

    const rawToken = match[1] || match[2] || match[3] || '';
    const token = normalizeToken(rawToken);

    if (!token) {
      nodes.push({
        type: 'text',
        text: match[0],
        marks: node.marks,
      });
    } else {
      nodes.push({
        type: mapVariableNodeType(token),
        attrs: {
          field: token,
          label: token.replace(/_/g, ' '),
          normalized: `<${token}>`,
          source_format: match[0].startsWith('<')
            ? 'ANGLE'
            : match[0].startsWith('{{')
              ? 'DOUBLE_BRACE'
              : 'BRACE',
        },
      });
    }

    cursor = index + match[0].length;
  }

  if (!nodes.length) {
    return [node];
  }

  if (cursor < text.length) {
    nodes.push({
      type: 'text',
      text: text.slice(cursor),
      marks: node.marks,
    });
  }

  return nodes;
};

const transformNode = (node: PMNode): PMNode[] => {
  if (isTextNode(node)) {
    return splitTextNodeToVariableNodes(node);
  }

  const normalizedNode: PMNode = {
    ...node,
  };

  if (node.type === 'dynamicTableVariable') {
    const token = String(node.attrs?.field || '').toUpperCase();
    const tableNode = DYNAMIC_TABLE_BY_TOKEN[token];
    if (tableNode) {
      return [tableNode];
    }
  }

  if (node.type === 'horizontalRule' && (node.attrs?.docxPageBreak || node.attrs?.pageBreak)) {
    normalizedNode.type = 'pageBreak';
    normalizedNode.attrs = {
      ...(node.attrs ?? {}),
      auto: false,
      source: 'docx',
    };
  }

  if (!node.content || !Array.isArray(node.content)) {
    return [normalizedNode];
  }

  const nextContent: PMNode[] = [];
  for (const child of node.content) {
    nextContent.push(...transformNode(child));
  }

  return [
    {
      ...normalizedNode,
      content: nextContent,
    },
  ];
};

export const normalizeDocForEnterpriseVariables = (doc: PMDoc): PMDoc => {
  const nextContent: PMNode[] = [];
  for (const node of doc.content || []) {
    nextContent.push(...transformNode(node));
  }

  return {
    ...doc,
    content: nextContent.length ? nextContent : [{ type: 'paragraph' }],
  };
};

const nodeTextLength = (node: PMNode): number => {
  if (isTextNode(node)) {
    return (node.text || '').length;
  }
  return (node.content || []).reduce((sum, child) => sum + nodeTextLength(child), 0);
};

const estimateTableHeight = (node: PMNode): number => {
  const rows = (node.content || []).filter((child) => child.type === 'tableRow').length;
  const minRows = Math.max(rows, 1);
  return 36 + minRows * 34;
};

const estimateBlockHeight = (node: PMNode): number => {
  switch (node.type) {
    case 'heading': {
      const level = Number(node.attrs?.level || 1);
      const lineHeight = level <= 1 ? 46 : level === 2 ? 38 : 32;
      const textLength = Math.max(nodeTextLength(node), 1);
      const wrappedLines = Math.max(1, Math.ceil(textLength / 70));
      return lineHeight + (wrappedLines - 1) * Math.max(24, lineHeight * 0.6);
    }
    case 'paragraph': {
      const textLength = nodeTextLength(node);
      const wrappedLines = Math.max(1, Math.ceil(Math.max(textLength, 1) / 95));
      return 14 + wrappedLines * 24;
    }
    case 'bulletList':
    case 'orderedList': {
      const items = (node.content || []).length;
      return 20 + Math.max(items, 1) * 28;
    }
    case 'table':
      return estimateTableHeight(node);
    case 'image':
      return Number(node.attrs?.height || 220);
    case 'horizontalRule':
    case 'pageBreak':
      return 20;
    default: {
      const textLength = nodeTextLength(node);
      if (textLength > 0) {
        return 20 + Math.max(1, Math.ceil(textLength / 95)) * 24;
      }
      return 28;
    }
  }
};

const isManualPageBreak = (node: PMNode): boolean => node.type === 'pageBreak' && node.attrs?.auto !== true;

const isHeading = (node: PMNode): boolean => node.type === 'heading';

const isLikelySignatureBlock = (node: PMNode): boolean => {
  if (node.type !== 'paragraph') {
    return false;
  }
  const text = flattenText(node).toUpperCase();
  return text.includes('AUTHORISED SIGNATORY') || text.includes('AUTHORIZED SIGNATORY') || text.includes('SIGNATURE');
};

const flattenText = (node: PMNode): string => {
  if (isTextNode(node)) {
    return node.text || '';
  }
  return (node.content || []).map((child) => flattenText(child)).join(' ');
};

const splitLongTable = (tableNode: PMNode, remainingHeight: number, printableHeight: number): PMNode[] | null => {
  if (tableNode.type !== 'table') {
    return null;
  }

  const rows = (tableNode.content || []).filter((node) => node.type === 'tableRow');
  if (rows.length <= 8) {
    return null;
  }

  const rowHeight = 34;
  const tableChrome = 24;
  const headerRows: PMNode[] = [];
  let bodyStart = 0;

  for (let i = 0; i < rows.length; i += 1) {
    const row = rows[i];
    const hasHeaderCell = (row.content || []).some((cell) => cell.type === 'tableHeader');
    if (hasHeaderCell) {
      headerRows.push(row);
      bodyStart = i + 1;
    } else {
      break;
    }
  }

  const bodyRows = rows.slice(bodyStart);
  const firstPageAvailableRows = Math.floor(Math.max(remainingHeight - tableChrome, rowHeight) / rowHeight);
  const nextPageAvailableRows = Math.floor(Math.max(printableHeight - tableChrome, rowHeight) / rowHeight);

  if (firstPageAvailableRows <= headerRows.length || nextPageAvailableRows <= headerRows.length) {
    return null;
  }

  if (bodyRows.length <= firstPageAvailableRows - headerRows.length) {
    return null;
  }

  const fragments: PMNode[] = [];
  let bodyIndex = 0;
  let rowsForCurrentPage = firstPageAvailableRows - headerRows.length;

  while (bodyIndex < bodyRows.length) {
    const chunk = bodyRows.slice(bodyIndex, bodyIndex + rowsForCurrentPage);
    const fragmentRows = [...headerRows, ...chunk];
    fragments.push({
      ...tableNode,
      content: fragmentRows,
    });

    bodyIndex += chunk.length;
    rowsForCurrentPage = nextPageAvailableRows - headerRows.length;

    if (bodyIndex < bodyRows.length) {
      fragments.push({
        type: 'pageBreak',
        attrs: { auto: true, source: 'table-split' },
      });
    }
  }

  return fragments;
};

const clearAutoPageBreaks = (nodes: PMNode[]): PMNode[] =>
  nodes.filter((node) => !(node.type === 'pageBreak' && node.attrs?.auto === true));

export const autoPaginateDoc = (doc: PMDoc, config: PaginationConfig): PMDoc => {
  const base = PAGE_DIMENSIONS[config.pageSize];
  const pageHeight = config.orientation === 'LANDSCAPE' ? base.width : base.height;
  const printableHeight = Math.max(180, pageHeight - config.marginPx * 2 - 28);

  const sourceNodes = clearAutoPageBreaks(doc.content || []);
  const paginated: PMNode[] = [];
  let remainingHeight = printableHeight;

  for (let i = 0; i < sourceNodes.length; i += 1) {
    const node = sourceNodes[i];

    if (isManualPageBreak(node)) {
      paginated.push(node);
      remainingHeight = printableHeight;
      continue;
    }

    const estimatedHeight = estimateBlockHeight(node);

    const nextNode = sourceNodes[i + 1];
    if (isHeading(node) && nextNode) {
      const headingClusterHeight = estimatedHeight + estimateBlockHeight(nextNode);
      if (headingClusterHeight > remainingHeight && paginated.length > 0) {
        paginated.push({
          type: 'pageBreak',
          attrs: { auto: true, source: 'heading-keep-with-next' },
        });
        remainingHeight = printableHeight;
      }
    }

    if ((node.type === 'table' || isLikelySignatureBlock(node)) && estimatedHeight > remainingHeight && paginated.length > 0) {
      paginated.push({
        type: 'pageBreak',
        attrs: { auto: true, source: 'keep-together' },
      });
      remainingHeight = printableHeight;
    }

    if (node.type === 'table') {
      const tableSplit = splitLongTable(node, remainingHeight, printableHeight);
      if (tableSplit) {
        for (const splitNode of tableSplit) {
          if (splitNode.type === 'pageBreak') {
            paginated.push(splitNode);
            remainingHeight = printableHeight;
            continue;
          }
          paginated.push(splitNode);
          remainingHeight -= estimateBlockHeight(splitNode);
        }
        continue;
      }
    }

    if (estimatedHeight > remainingHeight && paginated.length > 0) {
      paginated.push({
        type: 'pageBreak',
        attrs: { auto: true, source: 'overflow' },
      });
      remainingHeight = printableHeight;
    }

    paginated.push(node);
    remainingHeight -= estimateBlockHeight(node);
  }

  return {
    ...doc,
    content: paginated.length ? paginated : [{ type: 'paragraph' }],
  };
};

export const extractMarginPxFromLayout = (margins?: LayoutMargins): number | null => {
  if (!margins) {
    return null;
  }

  const topPt = Number(margins.top || 0);
  const bottomPt = Number(margins.bottom || 0);
  if (!Number.isFinite(topPt) || !Number.isFinite(bottomPt) || (topPt <= 0 && bottomPt <= 0)) {
    return null;
  }

  const averagePt = (Math.max(topPt, 0) + Math.max(bottomPt, 0)) / 2;
  const px = averagePt * (96 / 72);
  return Math.max(16, Math.min(140, Math.round(px)));
};
