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

First set up the appropriate AWS profile for chalice to use to connect to AWS by running `aws configure --profile chalice`.
Then run `export AWS_PROFILE=chalice` to use the chalice profile as the default when running `chalice local`.

Run `chalice local` to start local version of api's. Use ngrok(`https://ngrok.com/`) to expose the chalice server to the internet by running: `./ngrok http 8000`. You can now hit the ngrok endpoint with either curl or httpie(`https://httpie.org/`) locally to trigger the functions. 

For the frontend run `yarn start`

## Deployment

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
