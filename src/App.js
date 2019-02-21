import React, { Component } from 'react';
import logo from './logo.svg';
import './App.css';
import Container from './Container';
import MessageSetForm from './MessageSetForm';

class App extends Component {
  constructor (props) {
    super(props)
    this.state = {currentTab: 'table'
    }
  }
  onClick(tab){
    this.setState({currentTab:tab});
  }


  render() {
    var display = this.state.currentTab === 'table' ? <Container /> :  <MessageSetForm />
    return (
      <div className="App">
        <div className="App-header">
          <img src={logo} className="App-logo" alt="logo" />
          <h2>Welcome to Motivora</h2>
        </div>
        <p className="App-intro">
          Click the tabs below to view different Tables
        </p>
        <div className="col-md-9 col-md-offset-3">
          <MainNavbar currentTab={this.state.currentTab} onClick={this.onClick.bind(this)} />
        </div>
        <div>
          {display}
        </div>

      </div>

    );
  }
}

class MainNavbar extends Component {

  constructor (props) {
    super(props)
    this.state = {};
  }

  render() {
    console.log(this.props.currentTab);
    var tabs = [];
    if (this.props.currentTab === 'table'){
      tabs.push(
        <li key={1} role="presentation" onClick={() => { this.props.onClick('table') }} className="active col-md-3">
          <a href="#">Table</a>
        </li>
      );
    }
    else{
      tabs.push(
        <li key={2} role="presentation" onClick={() => { this.props.onClick('table') }} className=" col-md-3">
          <a href="#">Table</a>
        </li>
      );
    }
    if (this.props.currentTab === 'messagesetform'){
      tabs.push(
        <li key={3} role="presentation" onClick={() => { this.props.onClick('messagesetform') }} className="active col-md-3">
        <a href="#">Add Message Set</a>
        </li>
      );
    }
    else{
      tabs.push(
        <li key={4} role="presentation" onClick={() => { this.props.onClick('messagesetform') }} className=" col-md-3">
        <a href="#">Add Message Set</a>
        </li>
      );
    }
    return (
      <div className='nav-bar'>
        <ul className="nav nav-pills col-md-12">
          {tabs}
        </ul>
      </div>
    );
  }
}

export default App;
