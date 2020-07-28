import React, { Component } from 'react';
import Container from './Container';
import MessageSetForm from './MessageSetForm';
import { Navbar, Nav, Button } from 'react-bootstrap';
import './App.css';
import { withAuthenticator, AmplifySignOut } from '@aws-amplify/ui-react';

class App extends Component {

  constructor (props) {
    super(props)
    this.state = {
      activePage: 'USERS'
    }
  }

  renderActivePage() {
    switch(this.state.activePage){
      case 'ADD_MESSAGE':
        return(
          <div>
            <h2 id="page-title">Add Message Set</h2>
            <MessageSetForm/>
          </div>
        );
      case 'USERS':
        return(
          <div>
            <h2 id="page-title">All participants</h2>
            <Container activePage={this.state.activePage}/>
          </div>
        );
      case 'MESSAGES':
        return(
          <div>
            <h2 id="page-title">All messages</h2>
            <Container activePage={this.state.activePage}/>
          </div>
        );
      default:
        console.error('No activePage');
    }
  }

  render() {
    return (
      <div className="App">
        <Navbar bg="primary" variant="dark">
          <Navbar.Brand href="#home">Motivora</Navbar.Brand>
          <Nav className="mr-auto">
            <Nav.Link href="#users" onClick={() => { this.setState({activePage: 'USERS'}) }}>Participants</Nav.Link>
            <Nav.Link href="#messages" onClick={() => { this.setState({activePage: 'MESSAGES'}) }}>Messages</Nav.Link>
            <Button href="#add-message-set" onClick={() => { this.setState({activePage: 'ADD_MESSAGE'})  }}>Add Message Set</Button>
            <AmplifySignOut />
          </Nav>
        </Navbar>
        <div>
          {this.renderActivePage()}
        </div>
      </div>
    );
  }
}

export default withAuthenticator(App);
