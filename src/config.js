
const endpoint = (process.env.NODE_ENV === "development") ?
	"http://127.0.0.1:8000" 
		:
	"https://sj0fyj60d0.execute-api.us-east-1.amazonaws.com/api";

const Config = {
  api: endpoint
};

export default Config;
