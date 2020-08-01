import React, { Component } from 'react';
import Config from './config';
import axios from 'axios';
import loader from './images/ajax-loader.gif';


class MessageDetails extends Component {
	constructor(props) {
		super(props);
	}
	render() {
		return (
			<div>
				<h2>Message details</h2>
			</div>
		)
	}
}

export default MessageDetails