import { Box, Chip } from '@mui/material';

interface TokenRendererProps {
  text: string;
  fontSize?: number;
  fontWeight?: string;
  fontStyle?: string;
  textDecoration?: string;
  color?: string;
  align?: 'left' | 'center' | 'right' | 'justify';
}

/**
 * Token Renderer Component
 * 
 * Renders text with inline variable tokens styled as blue chips.
 * Similar to Zoho Creator's field token display.
 * 
 * Parses text like:
 *   "Hello {{customer_name}}, your loan amount is {{loan_amount}}"
 * 
 * And renders as:
 *   "Hello < customer_name >, your loan amount is < loan_amount >"
 * 
 * With tokens styled as blue chips.
 */
export function TokenRenderer({
  text,
  fontSize = 14,
  fontWeight = '400',
  fontStyle = 'normal',
  textDecoration = 'none',
  color = '#000',
  align = 'left',
}: TokenRendererProps) {
  // Parse text and split by {{variable}} tokens
  const parts: Array<{ type: 'text' | 'token'; content: string }> = [];
  let lastIndex = 0;
  const tokenRegex = /\{\{\s*([^}]+?)\s*\}\}/g;
  let match;

  while ((match = tokenRegex.exec(text)) !== null) {
    // Add text before token
    if (match.index > lastIndex) {
      parts.push({
        type: 'text',
        content: text.slice(lastIndex, match.index),
      });
    }
    
    // Add token
    parts.push({
      type: 'token',
      content: match[1], // The variable name without {{}}
    });
    
    lastIndex = match.index + match[0].length;
  }

  // Add remaining text
  if (lastIndex < text.length) {
    parts.push({
      type: 'text',
      content: text.slice(lastIndex),
    });
  }

  // If no tokens found, just render plain text
  if (parts.length === 0 || (parts.length === 1 && parts[0].type === 'text')) {
    return (
      <span
        style={{
          fontSize,
          fontWeight,
          fontStyle,
          textDecoration,
          color,
          textAlign: align,
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-word',
        }}
      >
        {text}
      </span>
    );
  }

  return (
    <Box
      component="span"
      sx={{
        fontSize,
        fontWeight,
        fontStyle,
        textDecoration,
        color,
        textAlign: align,
        display: 'inline',
        whiteSpace: 'pre-wrap',
        wordBreak: 'break-word',
      }}
    >
      {parts.map((part, index) => {
        if (part.type === 'token') {
          return (
            <Chip
              key={index}
              label={`< ${part.content} >`}
              size="small"
              sx={{
                height: 'auto',
                fontSize: fontSize * 0.9,
                fontWeight: 500,
                px: 0.5,
                py: 0.25,
                mx: 0.25,
                my: 0.125,
                bgcolor: '#e3f2fd',
                color: '#1976d2',
                border: '1px solid #90caf9',
                display: 'inline-flex',
                verticalAlign: 'baseline',
                '& .MuiChip-label': {
                  px: 1,
                  py: 0,
                  lineHeight: 1.5,
                },
              }}
            />
          );
        }
        return <span key={index} style={{ whiteSpace: 'pre-wrap' }}>{part.content}</span>;
      })}
    </Box>
  );
}
