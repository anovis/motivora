# motivora
serverless text platform

## Configs

create a `.chalice` folder in the root directory of the project and add this to file `config.json`
```
{
  "version": "2.0",
  "app_name": "motivora",
  "manage_iam_role": false,
  "iam_role_arn": "arn:aws:iam::ACOUNT_ID:role/ROLE_NAME",
  "environment_variables":{
    "SID":"TWILIO SID",
    "TOKEN" : "TWILIO TOKEN",
    "PHONE" : "TWILIO PHONE NUMBER"
  },
  "lambda_timeout": 900, //15 minutes
  "lambda_memory_size": 1024, //1024 MB
  "stages": {
    "dev": {
      "api_gateway_stage": "api"
    }
  }
}
```

## Run locally

### Chalice (Lambda functions)

First set up the appropriate AWS profile for chalice to use to connect to AWS by running `aws configure --profile chalice`.

Then run `npm run chalice-local` to start local version of api's.

Use ngrok(`https://ngrok.com/`) to expose the chalice server to the internet by running: `./ngrok http 8000`. You can now hit the ngrok endpoint with either curl or httpie (`https://httpie.org/`) locally to trigger the functions.

So essentially:
1. In a new terminal window run `npm run chalice-local`
3. In another new terminal window run `./ngrok http 8000`
4. In another new terminal window run `http http://b87c4337.ngrok.io/test` where `/test` is some test endpoint that you can add in the `frontend.py` file for local testing of specific parts of the functions. Where `http` is from [HTTPie](https://httpie.org/) (use it, it's awesome).

### Front end React app

For the frontend run `yarn start`

## Deployment

#### Deploy Frontend and Backend at once
run `npm run deploy` or `npm run deploy -- --git-tag` to also tag the release.

#### Frontend only (no git tag created)

run `export AWS_PROFILE=chalice && export AWS_DEFAULT_REGION=us-east-1 && npm install && npm run build && aws s3 sync build/ s3://motivora-website`

#### Lambdas (no git tag created)

run `export AWS_PROFILE=chalice && export AWS_DEFAULT_REGION=us-east-1 && chalice deploy` to deploy api gateway and lambdas.

#### Twilio

* create account and buy number
* set the sms webhook to the api gateway arn

## User Flow

*  text join to twilio number
*  prompted for time to receive messages (0-24)
*  receive texts daily and respond with number (0-10) on how much you liked it

## Upload messages to dynamo in bulk

Everything you need is in the ./scripts/dynamo_csv_upload/ folder

1. Save your raw CSV as raw_data.csv (needs to be the same format/columns as raw_data.csv.example)
2. While in the /dynamo_csv_upload folder, run `npm i` and then run `sh upload_messages.sh`
3. Check dynamo to make sure that your data got saved.
