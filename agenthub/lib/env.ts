export const inDevEnvironment = !!process && process.env.NODE_ENV === 'development';
// export const serverUrl = inDevEnvironment ? 'http://localhost:8000' : 'https://myapp-y5z35kuonq-uk.a.run.app'
export const baseUrl = inDevEnvironment ? 'http://localhost:3000' : 'https://my.aios.foundation'
// export const serverUrl = inDevEnvironment ? 'http://localhost:8000' : 'http://35.232.56.61:8000'
export const serverUrl = 'http://35.232.56.61:8000';

