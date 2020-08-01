import React, { Component } from 'react';
import PageContainer from './PageContainer';
import UserDetails from './UserDetails';
import MessageDetails from './MessageDetails';
import MessageSetForm from './MessageSetForm';
import CsvUploads from './CsvUploads';
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

	render() {
		return (
			<Router>
			<div className="App">
				<Navbar bg="primary" variant="dark">
					<Navbar.Brand href="/">Motivora</Navbar.Brand>
					<Nav className="mr-auto">
						<Nav.Link href="/users">Participants</Nav.Link>
						<Nav.Link href="/messages">Messages</Nav.Link>
						<Nav.Link href="/uploads">Uploads</Nav.Link>
						<AmplifySignOut />
					</Nav>
				</Navbar>
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
					<Route path="/uploads" component={CsvUploads}/> 
					<Route path="/add-message-set">
						<div>
							<h4 id="page-title">Add Message Set</h4>
							<MessageSetForm/>
						</div>
					</Route>
					<Route path="/user-details/:phone" component={UserDetails}/> 
					<Route path="/message-details/:id" component={MessageDetails}/> 
				</Switch>
			</div>
			</Router>
		);
	}
}

export default withAuthenticator(App);
