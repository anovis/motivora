import React, { Component } from 'react';
import Config from './config';
import axios from 'axios';
import loader from './images/ajax-loader.gif';
import { Container, Col, Row } from 'react-bootstrap';


class MessageDetails extends Component {
	constructor(props) {
		super(props);
		this.state = {
			loadingData: false
		}
		this.fetchData = this.fetchData.bind(this);
	}
	componentDidMount() {
		this.fetchData(this.props.message);
	}

	componentWillReceiveProps(nextProps) {
		if (nextProps.message) {
			this.fetchData(nextProps.message);
		}
	}
	fetchData(message) {
		
		let endpoint = Config.api + '/messages/get_stats';
		let params = {
			params: {
				message_set: message.message_set,
				id: message.id
			}
		}
		this.setState({loadingData: true});
		axios.get(endpoint, params)
			.then((response) => {
				if (response.data) {
					this.setState({
						average_rating: response.data.average_rating,
						total_rated: response.data.total_rated,
						total_sent: response.data.total_sent,
						loadingData: false,
					});
				}
			})
			.catch((error) => {
				window.alert(error)
				this.setState({
					loadingData: false,
				});
			})
	}
	render() {
		let style = {
			padding: '20px'
		}
		return (this.state.loadingData) ? (
			<div className="ajax-loader-container">
				<img src={loader} alt="Loader"/>
			</div>
		) : (
			<Container style={ style }>
				<ul className="list-unstyled">
					<li>Sent { this.state.total_sent } times</li>
					<li>Rated { this.state.total_rated } times </li>
					<li>Average rating: { this.state.average_rating }</li>
				</ul>
			</Container>
		)
	}
}

export default MessageDetails