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
  "stages": {
    "dev": {
      "api_gateway_stage": "api"
    }
  }
}
```

## Test locally

run `chalice local` to start local version of api's. if you want to interact with it via twilio then use
ngrok to mock an endpoint and forward to localhost:8000.
`https://ngrok.com/`

for the frontend run `yarn start`

## Deployment

#### Deploy Frontend and Backend at once
run `npm run deploy` or `npm run deploy --git-tag` to also tag the release.

#### Frontend

* run `yarn build` then copy all components of the build folder to s3. make sure the make the s3 folder public.
* TODO (right now i hard coded the api gateway address, but this should be in a config to trigger between localhost and api gateway)

#### Lambdas

* run `chalice deploy` to deploy api gateway and lambdas.

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
