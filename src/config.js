
const endpoint = process.env.NODE_ENV === "production" ?
   "localhost:3000" :
   "https://5b36vt9t44.execute-api.us-east-1.amazonaws.com/api";

const Config = {
  api: endpoint
};

export default Config;
