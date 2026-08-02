import React from 'react';
import { useSelection } from '../../contexts/SelectionContext';
import PageToolbar from './PageToolbar';
import ParagraphToolbar from './ParagraphToolbar';
import FieldToolbar from './FieldToolbar';
import TableToolbar from './TableToolbar';
import ImageToolbar from './ImageToolbar';
import QRCodeToolbar from './QRCodeToolbar';
import BarcodeToolbar from './BarcodeToolbar';
import HeaderToolbar from './HeaderToolbar';
import FooterToolbar from './FooterToolbar';
import RectangleToolbar from './RectangleToolbar';
import LineToolbar from './LineToolbar';
import SignatureToolbar from './SignatureToolbar';
import LogoToolbar from './LogoToolbar';

const ToolbarManager: React.FC = () => {
  const { selectedType } = useSelection();

  switch (selectedType) {
    case 'PAGE':
      return <PageToolbar />;
    case 'PARAGRAPH':
      return <ParagraphToolbar />;
    case 'FIELD':
      return <FieldToolbar />;
    case 'TABLE':
      return <TableToolbar />;
    case 'IMAGE':
      return <ImageToolbar />;
    case 'QR':
        return <QRCodeToolbar />;
    case 'BARCODE':
        return <BarcodeToolbar />;
    case 'HEADER':
        return <HeaderToolbar />;
    case 'FOOTER':
        return <FooterToolbar />;
    case 'RECTANGLE':
        return <RectangleToolbar />;
    case 'LINE':
        return <LineToolbar />;
    case 'SIGNATURE':
        return <SignatureToolbar />;
    case 'LOGO':
        return <LogoToolbar />;
    default:
      return <PageToolbar />; // Default to PageToolbar
  }
};

const ContextToolbar: React.FC = () => {
  return (
    <div style={{ padding: '8px', borderBottom: '1px solid #ccc' }}>
      <ToolbarManager />
    </div>
  );
};

export default ContextToolbar;
