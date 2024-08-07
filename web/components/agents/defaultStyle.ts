export default {
    control: {
      backgroundColor: 'transparent',
      fontSize: 14,
      fontWeight: 'normal',
      width: '100%',
    },
  
    '&multiLine': {
      control: {
        fontFamily: 'monospace',
        // minHeight: 63,
        maxHeight: 200
      },
      highlighter: {
        padding: 3,
        border: '1px solid transparent',
      },
      input: {
        padding: 3,
        border: '1px solid transparent',
        outline: '2px solid transparent',
      outlineOffset: '2px',
      },
    },
  
    suggestions: {
      list: {
        backgroundColor: 'white',
        border: '1px solid rgba(0,0,0,0.15)',
        fontSize: 14,
      },
      item: {
        padding: '5px 15px',
        borderBottom: '1px solid rgba(0,0,0,0.15)',
        '&focused': {
          backgroundColor: '#cee4e5',
        },
      },
    },
  }