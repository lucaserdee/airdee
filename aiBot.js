const axios = require('axios');

async function queryWeaviate(vector) {
  if (!Array.isArray(vector) || vector.some(v => typeof v !== 'number')) {
    throw new Error('Input vector must be an array of numbers');
  }
  try {
    const response = await axios.post('https://welz4ghqqeynlanof5qemg.c0.europe-west3.gcp.weaviate.cloud/v1/graphql', {
      query: `{
        Get {
          YourClass(
            nearVector: {
              vector: [${vector.join(',')}],
              certainty: 0.7
            }
          ) {
            content
            source
            extraField1
            extraField2
          }
        }
      }`
    });
    if (
      response.data &&
      response.data.data &&
      response.data.data.Get &&
      response.data.data.Get.YourClass
    ) {
      return response.data.data.Get.YourClass;
    } else {
      throw new Error('Unexpected response format from Weaviate');
    }
  } catch (error) {
    console.error('Weaviate query failed:', error.message);
    return [];
  }
}

module.exports = { queryWeaviate };