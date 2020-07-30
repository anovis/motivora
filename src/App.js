import React, { Component } from 'react';
import PageContainer from './PageContainer';
import UserDetails from './UserDetails';
import MessageSetForm from './MessageSetForm';
import { CSVReader } from 'react-papaparse';
import { Container, Col, Row } from 'react-bootstrap';
import { 
	Navbar, 
	Nav, 
	Button 
} from 'react-bootstrap';
import './App.css';
import { 
	withAuthenticator, 
	AmplifySignOut 
} from '@aws-amplify/ui-react';
import {
	BrowserRouter as Router,
	Switch,
	Route
} from "react-router-dom";

class App extends Component {

	constructor (props) {
		super(props)
		this.state = {
			activePage: 'USERS'
		}
	}
	handleOnDropCsvFile(data) {
		console.log('---------------------------')
		console.log(data)
		console.log('---------------------------')
	}

	handleOnErrorCsvFile(err, file, inputElem, reason) {
		console.log(err)
	}

	handleOnRemoveCsvFile(data) {
		console.log('---------------------------')
		console.log(data)
		console.log('---------------------------')
	}

	render() {
		return (
			<Router>
			<div className="App">
				<Navbar bg="primary" variant="dark">
					<Navbar.Brand href="/">Motivora</Navbar.Brand>
					<Nav className="mr-auto">
						<Nav.Link href="/users">Participants</Nav.Link>
						<Nav.Link href="/messages">Messages</Nav.Link>
						<Button href="/add-message-set">Add Message Set</Button>
						<AmplifySignOut />
					</Nav>
				</Navbar>
				<Container style={{ padding: '20px' }}>
					<Row>
						<Col xs={4}>
							<CSVReader
								onDrop={this.handleOnDropCsvFile}
								onError={this.handleOnErrorCsvFile}
								addRemoveButton
								onRemoveFile={this.handleOnRemoveCsvFile}
								config={{
									header: true,
								}}
							>
								<span>Drop CSV file here or click to add message ratings.</span>
							</CSVReader>
						</Col>
					</Row>
				</Container>
				<hr/>
				<Switch>
					<Route path="/users">
						<div>
							<h4 id="page-title">All participants</h4>
							<PageContainer activePage="USERS"/>
						</div>
					</Route>
					<Route path="/messages">
						<div>
							<h4 id="page-title">All messages</h4>
							<PageContainer activePage="MESSAGES"/>
						</div>
					</Route>
					<Route path="/add-message-set">
						<div>
							<h4 id="page-title">Add Message Set</h4>
							<MessageSetForm/>
						</div>
					</Route>
					<Route path="/user-details/:phone" component={UserDetails}/> 
				</Switch>
			</div>
			</Router>
		);
	}
}

export default withAuthenticator(App);
