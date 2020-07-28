import React from 'react';
import ReactDOM from 'react-dom';
import App from './App';
import 'bootstrap/dist/css/bootstrap.css';
import './index.css';
import Amplify from 'aws-amplify';

Amplify.configure({
    Auth: {
        // REQUIRED - Amazon Cognito Region
        region: 'US-EAST-1',
        // OPTIONAL - Amazon Cognito User Pool ID
        userPoolId: 'us-east-1_5ebUvVWSn',

        // OPTIONAL - Amazon Cognito Web Client ID (26-char alphanumeric string)
        userPoolWebClientId: '7sqkmguvlu3q7s88s8f1o0hhkn',

    }
});

ReactDOM.render(
  <App />,
  document.getElementById('root')
);
