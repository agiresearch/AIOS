export default {
    control: {
      backgroundColor: 'inherit',
      fontSize: 14,
      fontWeight: 'normal',
      width: '100%',
      flexGrow: 1,
      // padding: '0.5rem',
      // borderColor: 'white',
      // borderRadius: '1rem',
      // borderWidth:'1px',
      // borderStyle: 'solid',
      // display: 'flex',
      // alignItems: 'center',
      // justifyContent: 'center',
      // position: 'relative'
    },

    // input: {
    //   left: '50%',
    //   top: '50%',
    //   transform: 'translate(-50%, -50%)',
    // },
  
    '&multiLine': {
      control: {
        fontFamily: 'monospace',
        // minHeight: 63,
        maxHeight: 150
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
        backgroundColor: '#3c3937',
        border: '1px solid rgba(0,0,0,0.15)',
        fontSize: 14,
        // color: 'white'
      },
      item: {
        padding: '5px 15px',
        borderBottom: '1px solid rgba(0,0,0,0.15)',
        '&focused': {
          backgroundColor: '#4acb91',
        },
      },
    },
  }