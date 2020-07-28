import React, { Component } from 'react';
import { Button, Form } from 'react-bootstrap';
import Modal from 'react-bootstrap4-modal';
import PropTypes from 'prop-types';
import Config from './config';
import axios from 'axios';

class SendMessageModal extends Component {
	constructor (props) {
		super(props);
		this.state = {
			show: props.show,
			phone: props.phone,
			smsBody: ''
		};
		this.parentCallback = this.props.onClose;
  		this.handleClose = this.handleClose.bind(this);
  		this.handleSubmit = this.handleSubmit.bind(this);
  		this.handleChange = this.handleChange.bind(this);
	}
	handleChange(event) {
    	const target = event.target;
    	const value = target.value;
    	const name = target.name;
    	this.setState({
      		[name]: value
    	});
  	}
	handleClose() {
		if (this.parentCallback) {
			this.parentCallback();
		}
		this.setState({
			show: false,
			phone: null,
			smsBody: ''
		})
	}
  	handleSubmit(event) {
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
	    	_this.handleClose();
	    })
	    .catch(error => {
	        window.alert('An error occured on the server. Please ensure that the phone number provided is correct');
	    });
	    event.preventDefault();
  	}
  	componentWillReceiveProps(nextProps) {
		this.setState({
			show: nextProps.show,
			phone: nextProps.phone,
		})
	}
	render() {
		return (
			<Modal fade={false} visible={this.state.show} onClickBackdrop={this.handleClose}>
				<div className="modal-header">
          			<h5 className="modal-title">Send a message to { this.state.phone }</h5>
        		</div>
        		<div className="modal-body">
          			<Form>
          				<Form.Group controlId="messageBody">
    						<Form.Label>Please enter your message here</Form.Label>
    						<Form.Control 
    							as="textarea" 
    							rows="4"
    							name="smsBody"
    							value={this.state.smsBody}
    							onChange={this.handleChange}
    						/>
  						</Form.Group>
					</Form>
        		</div>
        		<div className="modal-footer">
          			<button type="button" className="btn btn-secondary" onClick={this.handleClose}>
            			Close
          			</button>
          			<button type="button" className="btn btn-primary" onClick={this.handleSubmit}>
            			Send message
          			</button>
        		</div>
      		</Modal>
		);
	}

}


SendMessageModal.propTypes = {
	show: PropTypes.bool.isRequired,
	phone: PropTypes.number
}


export default SendMessageModal;