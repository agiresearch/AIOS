export const retryOperation = async (operation: any, maxRetries = 10, delay = 1000) => {
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        return await operation();
      } catch (error: any) {
        if (error.response && error.response.status === 504 && attempt < maxRetries) {
          console.log(`Attempt ${attempt} failed with 504 error. Retrying...`);
          await new Promise(resolve => setTimeout(resolve, delay));
        } else {
          throw error;
        }
      }
    }
  };
  