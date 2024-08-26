export const inDevEnvironment = !!process && process.env.NODE_ENV === 'development';
export const serverUrl = inDevEnvironment ? 'http://localhost:8000' : 'https://myapp-y5z35kuonq-uk.a.run.app'
// export const serverUrl = 'https://myapp-y5z35kuonq-uk.a.run.app';

