import React, { Component } from 'react';
import { Container, Col, Row, Badge, Form } from 'react-bootstrap';
import Config from './config';
import axios from 'axios';
import loader from './images/ajax-loader.gif';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faArrowLeft, faArrowRight } from '@fortawesome/free-solid-svg-icons';
import InputRange from 'react-input-range';
import 'react-input-range/lib/css/index.css';


class UserDetails extends Component {
	constructor(props) {
		super(props);
		this.state = {
			phone: props.match.params.phone,
			smsBody: '',
			messages: [],
			attrs: [],
			ranked_attrs: {},
			preferred_attrs: [],
			filters: {
				search: '',
				rating: {
					min: 0,
					max: 10
				},
				categories: {
					daily: true,
					direct: true,
					weekly_goals: true
				},
				directions: {
					incoming: true,
					outgoing: true
				},
				attributes: {}
			}
		};
		this.fetchMessageHistory = this.fetchMessageHistory.bind(this);
		this.fetchAttrs = this.fetchAttrs.bind(this);
  		this.handleTypeMessage = this.handleTypeMessage.bind(this);
  		this.handleSendMessage = this.handleSendMessage.bind(this);
  		this.formatTimestamp = this.formatTimestamp.bind(this);
  		this.onRatingFilter = this.onRatingFilter.bind(this);
  		this.onCategoryFilter = this.onCategoryFilter.bind(this);
  		this.onDirectionFilter = this.onDirectionFilter.bind(this);
  		this.onAttributeFilter = this.onAttributeFilter.bind(this);
  		this.onSearch = this.onSearch.bind(this);
  		this.filterMessages = this.filterMessages.bind(this);
  		this.roundNumber = this.roundNumber.bind(this);
	}
	componentDidMount() {
		this.fetchMessageHistory();
		this.fetchAttrs();
	}
	fetchMessageHistory() {
		let endpoint = Config.api + '/users/message_history';
		let params = {
			phone: this.state.phone
		}
		this.setState({loadingData: true});
		axios.get(endpoint, {params: params})
			.then((response) => {
				let attrs = [];
				response.data.data.map(message => {
					attrs = attrs.concat(message.attrs).motivoraUnique()
				});
				let filters = this.state.filters;
				attrs.map(attr => {
					filters.attributes[attr] = true;
				})
				console.log(filters)
				this.setState({
					messages: response.data.data,
					attrs: attrs,
					loadingData: false,
					filters: filters
				});
			})
			.catch((error) => {console.log(error)})
	}
	fetchAttrs() {
		let endpoint = Config.api + '/users/attrs';
		let params = {
			phone: this.state.phone
		}
		axios.get(endpoint, {params: params})
			.then((response) => {
				console.log(response)
				this.setState({
					ranked_attrs: response.data.data.ranked_attrs,
					preferred_attrs: response.data.data.preferred_attrs,
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
  	onCategoryFilter(event) {
	    let target = event.target;
	    let value = target.value;
	    let name = target.name;

  		let filters = this.state.filters;
  		filters.categories[name] = (value == 'false');
  		this.setState({filters: filters});
  	}
  	onSearch(event) {
	    let target = event.target;
	    let value = target.value;
	    let name = target.name;

  		let filters = this.state.filters;
  		filters.search = value;
  		this.setState({filters: filters});
  	}

  	onDirectionFilter(event) {
	    const target = event.target;
	    const value = target.value;
	    const name = target.name;
  		let filters = this.state.filters;
  		filters.directions[name] = (value == 'false');
  		this.setState({filters: filters});
  	}
  	onAttributeFilter(event) {
	    const target = event.target;
	    const value = target.value;
	    const name = target.name;
  		let filters = this.state.filters;
  		filters.attributes[name] = (value == 'false');
  		this.setState({filters: filters});
  	}

  	onRatingFilter(range) {
  		let _this = this;
  		let filters = this.state.filters;
  		filters.rating = range;
  		this.setState({filters: filters});
  	}
  	filterMessages() {
  		let _this = this;
  		return this.state.messages.filter(message => {
  			if ((message.rating < _this.state.filters.rating.min) || (message.rating > _this.state.filters.rating.max)) {
  				return false;
  			}
  			if (_this.state.filters.categories[message.category] === false) {
  				return false;
  			}
  			if (_this.state.filters.directions[message.direction] === false) {
  				return false;
  			}
  			let hasAttr = false;
  			for (let i = 0; i < (message.attrs || []).length; i++) {
  				let attr = (message.attrs || [])[i];
	  			if (_this.state.filters.attributes[attr] === true) {
	  				hasAttr = true;
	  				break;
	  			}
  			}
  			if (hasAttr === false) return false;
  			if (message.message && !message.message.includes(_this.state.filters.search)) {
  				return false;
  			}
  			if (message.body && !message.body.includes(_this.state.filters.search)) {
  				return false;
  			}
  			return true;
  		})
  	}
  	roundNumber(number) {
  		if (number) {
			var rounded = Math.round(number * 10) / 10;
			var fixed = rounded.toFixed(1);
			return parseFloat(number.toFixed(2))
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
				<div className="text-left" style={{ padding: '20px'}}>
					<Container>
						<Row>
							<Col xs={4}>
								<b>Participant: +{ this.state.phone }</b>
				    			<hr/>
								<b>Preferred attributes:</b>
								<ul>
									{
										this.state.preferred_attrs.map((attr, index) => 
											<li key={ index }><b>{ attr }</b></li>
										)
									}
								</ul>
				    			<hr/>
								<b>Ratings:</b>
								<ul>
									{
										Object.keys(this.state.ranked_attrs).map((key, index) => 
											<li key={ index }><b>{ key }</b>: <Badge variant={ this.getBadgeColor(this.roundNumber(this.state.ranked_attrs[key])) }>{ this.roundNumber(this.state.ranked_attrs[key]) }</Badge></li>
										)
									}
								</ul>
				    			<hr/>
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
            							Send message to participant
          							</button>
								</div>
								
							</Col>
							<Col xs={4}>
								<h4>{ (this.filterMessages() || []).length } messages displayed</h4>
								<div style={{ height: '500px', overflowY: 'auto' }}>
									{
										this.filterMessages().map((message, index) => 
											<div 
												key={index}
												role="alert" 
												className={`alert alert-${ this.getAlertColor(message) } text-${ this.getTextDirection(message) }`}
											>
												<b><i>{ this.formatTimestamp(message.timestamp) }</i> { (message.rating != null) ? <Badge variant={ this.getBadgeColor(message.rating) } className="pull-right">{ message.rating }</Badge> : null }</b>
												<span>
				  									{ (message.direction === 'outgoing') ? <FontAwesomeIcon icon={faArrowRight} size="xs"/> : null } 
				  									
				  									{ (message.direction !== 'outgoing') ? <FontAwesomeIcon icon={faArrowLeft} size="xs"/>  : null } 
				  								</span>
				  								<div>
					  								{
					  									(message.attrs || []).map((attr, j) => <Badge key={j} variant="secondary">{ attr }</Badge>)
					  								}
				  								</div>
												<p>
													{ message.body || message.message }
												</p>
											</div>
										)
									}
								</div>
							</Col>
							<Col xs={4}>
								<Form>
									<Form.Group>
				    					<Form.Label>Filter by rating:</Form.Label>
				    					<InputRange
        									maxValue={10}
        									minValue={0}
        									allowSameValues={true}
        									value={this.state.filters.rating}
        									onChange={ this.onRatingFilter } 
        								/>
				    				</Form.Group>
				    				<hr/>
									<Form.Group>
				    					<Form.Label>Search in messages:</Form.Label>
										<Form.Control 
											type="text" 
											name="search" 
											value={this.state.filters.search} 
											onChange={this.onSearch} 
										/>
				    					</Form.Group>
				    				<hr/>
									<Form.Group>
				    					<Form.Label>Filter by category:</Form.Label>
										<Form.Check
											required
        									checked={this.state.filters.categories.daily}
        									value={this.state.filters.categories.daily}
											name="daily"
											label="Daily message"
											onChange={ this.onCategoryFilter }
										/>
										<Form.Check
											required
        									checked={this.state.filters.categories.direct}
        									value={this.state.filters.categories.direct}
											name="direct"
											label="Direct message"
											onChange={ this.onCategoryFilter }
										/>
										<Form.Check
											required
        									checked={this.state.filters.categories.weekly_goals}
        									value={this.state.filters.categories.weekly_goals}
											name="weekly_goals"
											label="Weekly goals"
											onChange={ this.onCategoryFilter }
										/>
          							</Form.Group>
				    				<hr/>
									<Form.Group>
				    					<Form.Label>Filter by direction:</Form.Label>
										<Form.Check
											required
											name="outgoing"
											label="Sent by Motivora"
											onChange={ this.onDirectionFilter }
        									checked={this.state.filters.directions.outgoing}
        									value={this.state.filters.directions.outgoing}
										/>
										<Form.Check
											required
											name="incoming"
											label="Sent by participant"
											onChange={ this.onDirectionFilter }
        									checked={this.state.filters.directions.incoming}
        									value={this.state.filters.directions.incoming}
										/>
          							</Form.Group>
				    				<hr/>
									<Form.Group>
				    					<Form.Label>Filter by attribute:</Form.Label>
				    					{
				    						this.state.attrs.map((attr, index) => 
				    							<Form.Check
				    								key={ index }
													required
													name={ attr }
													label={ attr }
													onChange={ this.onAttributeFilter }
		        									checked={this.state.filters.attributes[attr]}
		        									value={this.state.filters.attributes[attr]}
												/>
											)
				    					}
										
          							</Form.Group>
								</Form>

							</Col>
						</Row>
					</Container>
				</div>
			)
		}
		
	}
}
Array.prototype.motivoraUnique = function() {
    var a = this.concat();
    for(var i=0; i<a.length; ++i) {
        for(var j=i+1; j<a.length; ++j) {
            if(a[i] === a[j])
                a.splice(j--, 1);
        }
    }

    return a;
};

export default UserDetails;