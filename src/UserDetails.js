import React, { Component } from 'react';
import { Container, Col, Row, Badge, Form } from 'react-bootstrap';
import Config from './config';
import axios from 'axios';
import loader from './images/ajax-loader.gif';


class UserDetails extends Component {
	constructor(props) {
		super(props);
		this.state = {
			phone: props.match.params.phone,
			smsBody: '',
			messages: []
		};
		this.fetchMessageHistory = this.fetchMessageHistory.bind(this);
  		this.handleTypeMessage = this.handleTypeMessage.bind(this);
  		this.handleSendMessage = this.handleSendMessage.bind(this);
  		this.formatTimestamp = this.formatTimestamp.bind(this);
	}
	componentDidMount() {
		this.fetchMessageHistory();
	}
	fetchMessageHistory() {
		let endpoint = Config.api + '/users/message_history';
		let params = {
			phone: this.state.phone
		}
		this.setState({loadingData: true});
		axios.get(endpoint, {params: params})
			.then((response) => {
				this.setState({
					messages: response.data.data,
					loadingData: false
				});
			})
			.catch((error) => {console.log(error)})
	}
	getAlertColor(message) {
		if (message.category === 'daily') {
			return 'success';
		} else if (message.category === 'direct') {
			return 'primary';
		} else if (message.category === 'weekly_goals') {
			return 'warning';
		}
	}
	getTextDirection(message) {
		return (message.direction === 'outgoing') ? 'left' : 'right'
	}
	handleTypeMessage(event) {
    	const target = event.target;
    	const value = target.value;
    	const name = target.name;
    	this.setState({
      		[name]: value
    	});
  	}
  	handleSendMessage(event) {
	    const _this = this;
	    axios.post(Config.api + '/users/send_message', {
	        phone_number: _this.state.phone,
	        message: _this.state.smsBody
	    })
	    .then(response => {
	    	if (response && response.status === 200) {
	        	window.alert('SMS successfully sent')
	    	} else {
	        	window.alert('An error occured on the server. Please ensure that the phone number provided is correct');
	    	}
	    	_this.fetchMessageHistory();
	    })
	    .catch(error => {
	        window.alert('An error occured on the server. Please ensure that the phone number provided is correct');
	    });
	    event.preventDefault();
  	}
  	formatTimestamp(date) {
  		if (date) {
	  		let options = {month: 'long', year: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit', timeZone: "America/New_York"};
	  		return (new Date(date)).toLocaleDateString('en-US', options);
  		}
  	}
  	getBadgeColor(rating) {
  		if (rating >= 8) {
  			return 'success';
  		} else if (rating >= 5 ) {
  			return 'warning';
  		} else {
  			return 'danger';
  		}
  	}

	render() {
		var messages = this.state.messages;
		if (this.state.loadingData){
			return (
				<div className="ajax-loader-container">
					<img src={loader} alt="Loader"/>
				</div>
			);
		} else {
			return (
				<div className="text-left">
					<Container>
						<Row>
							<Col>
								<h2 id="page-title">Participant: +{ this.state.phone }</h2>
							</Col>
						</Row>
						<hr/>
						<Row>
							<Col xs={4}>
							</Col>
							<Col xs={4}>
							</Col>
							<Col xs={4} style={{ height: '500px', overflowY: 'auto' }}>
								{
									this.state.messages.map((message, index) => 
										<div 
											key={index}
											role="alert" 
											className={`alert alert-${ this.getAlertColor(message) } text-${ this.getTextDirection(message) }`}
										>
											<h5><i>{ this.formatTimestamp(message.timestamp) }</i> { message.rating ? <Badge variant={ this.getBadgeColor(message.rating) } className="pull-right">{ message.rating }</Badge> : null }</h5>
											<div className="alert-heading h4">
			  									{ (message.direction === 'outgoing') ? <i className="glyphicon glyphicon-arrow-right"></i> : null } 
			  									
			  									{ (message.direction !== 'outgoing') ? <i className="glyphicon glyphicon-arrow-left"></i> : null } 
			  								</div>
											<p>
												{ message.body || message.message }
											</p>
										</div>
									)
								}
								<div>
									<Form>
				          				<Form.Group controlId="messageBody">
				    						<Form.Label>Please enter your message here</Form.Label>
				    						<Form.Control 
				    							as="textarea" 
				    							rows="4"
				    							name="smsBody"
				    							value={this.state.smsBody}
				    							onChange={this.handleTypeMessage}
				    						/>
				  						</Form.Group>
									</Form>
									<button type="button" className="btn btn-primary" onClick={this.handleSendMessage}>
            							Send message
          							</button>
								</div>
							</Col>
						</Row>
					</Container>
				</div>
		)
		}
		
	}
}

export default UserDetails;