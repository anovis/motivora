import React, { Component } from 'react';
import { Form, FormGroup, FormControl, Col, Button } from 'react-bootstrap';
import Config from './config';
import './MessageSetForm.css';
var axios = require('axios');

class MessageSetForm extends Component {
  constructor(props) {
    super(props);
    this.state = {
      MessageSetName: '',
      AttrNum:0,
      MessageNum:0
    };

    this.handleChange = this.handleChange.bind(this);
    this.handleSubmit = this.handleSubmit.bind(this);
    this.handleSelect = this.handleSelect.bind(this);
  }

  handleChange(event) {
    const target = event.target;
    const value = target.value;
    const name = target.name;
    this.setState({
      [name]: value
    });
  }

    handleSelect(event) {
    const target = event.target;
    const value = target.value;
    const name = target.name;
    this.setState((prevState) => {
      if (prevState[name] === undefined){
        return {[name]: [value]}
      }
      else{
        var index = prevState[name].indexOf(value);
        if (index > -1){
           prevState[name].splice(index, 1);
        }
        else{
          prevState[name].push(value)
        }
        return {[name]: prevState[name]};
      }
    });
  }

  formatNewMessagePayload() {
    let final = {
      messageSetName: this.state.MessageSetName,
      messages: []
    }
    for(let i = 0, l = parseInt(this.state.MessageNum); i < l; i++){
      const message = {
        message: this.state[`Message${i}`],
        attributes: this.state[`MessageAttr${i}`]
      };
      final.messages.push(message);
    }
    return final;
  }

  handleSubmit(event) {
    axios.post(Config.api + '/messages', {
        data: this.formatNewMessagePayload()
      })
      .catch(function (error) {
        console.log(error);
      });
    event.preventDefault();
  }

  renderAttributeSelections() {
    var optionGroups = [];
    for (let i = 0; i < this.state.AttrNum; i++){
      var attrName = 'Attr' + i;
      if(this.state[attrName]){
        optionGroups.push(
          <Form.Check
            key={attrName}
            type={'checkbox'}
            id={attrName}
            label={this.state[attrName]}
            inline
          />
        );
      }
    }
    return optionGroups.length ?
      <FormGroup controlId="formControlsSelectMultiple">
        <div>Select attributes for this message</div>
        {optionGroups}
      </FormGroup>
      :
      null;
  }

  renderAttributeInputs() {
    var AttrFormGroups = [];
    for (let i = 0; i < this.state.AttrNum; i++){
      var attrName = 'Attr' + i;
      AttrFormGroups.push(
        <FormGroup key={i} controlId={attrName}>
          <Col sm={2}>
            {attrName}
          </Col>
          <Col sm={10}>
            <FormControl type="text" name={attrName} value={this.state.attrName} onChange={this.handleChange} placeholder={attrName} />
          </Col>
        </FormGroup>
      );
    }
    return AttrFormGroups;
  }

  renderMessageInputs() {
    var MessageFormGroups = [];
    for (let i = 0; i < this.state.MessageNum; i++){
      var MessNum = 'Message' + i;
      var MessAttr = 'MessageAttr' + i;
      MessageFormGroups.push(
        <div key={i}>
          <FormGroup controlId={MessNum}>
            <Col sm={2}>
              {MessNum}
            </Col>
            <Col sm={10}>
              <FormControl type="text" name={MessNum} value={this.state.MessNum} onChange={this.handleChange} placeholder={MessNum + ' body'} />
            </Col>
          </FormGroup>
          {this.renderAttributeSelections()}
        </div>
      )
    }
    return MessageFormGroups;
  }

  render() {
    return (
      <Form id="add-message-form">
        <FormGroup controlId="formHorizontalName">
          <Col sm={2}>
            <b>Message Set Name</b>
          </Col>
          <Col sm={10}>
            <FormControl type="text" name='MessageSetName' value={this.state.MessageSetName} onChange={this.handleChange} placeholder="Message Set Name" />
          </Col>
        </FormGroup>
        <FormGroup controlId="formHorizontalAttrNum">
          <Col sm={2}>
            <b>Number of Attributes</b>
          </Col>
          <Col sm={10}>
            <FormControl type="number" name='AttrNum' value={this.state.AttrNum} onChange={this.handleChange} placeholder="Number of Attributes" />
          </Col>
        </FormGroup>
        {this.renderAttributeInputs()}
        <FormGroup controlId="formHorizontalText">
          <Col sm={2}>
            <b>Number of Messages</b>
          </Col>
          <Col sm={10}>
            <FormControl type="number" name='MessageNum' value={this.state.MessageNum} onChange={this.handleChange} placeholder="Number of Messages" />
          </Col>
        </FormGroup>
        {this.renderMessageInputs()}
        <FormGroup id="create-message-set-button">
          <Col sm={{ span: 10, offset: 1 }}>
            <Button type="submit" onClick={this.handleSubmit} size="lg">
              Create Message Set
            </Button>
          </Col>
        </FormGroup>
      </Form>
    );
  }
}

export default MessageSetForm;
