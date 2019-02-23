import React, { Component } from 'react';
import { Form, FormGroup, FormControl, Col, Button, ControlLabel } from 'react-bootstrap';
import Config from './config';
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


  render() {
    var AttrFormGroups = [];
    var optionGroups = [];
    for (let i = 0; i < this.state.AttrNum; i++){
      var attrName = 'Attr' + i;
      AttrFormGroups.push(
        <FormGroup key={i} controlId={attrName}>
          <Col componentClass={ControlLabel} sm={2}>
            {attrName}
          </Col>
          <Col sm={10}>
            <FormControl type="text" name={attrName} value={this.state.attrName} onChange={this.handleChange} placeholder={attrName} />
          </Col>
        </FormGroup>
      );
      optionGroups.push(
        <option key={i} value={this.state[attrName]}>{this.state[attrName]} </option>
      );
    }

    var MessageFormGroups = [];
    for (let i = 0; i < this.state.MessageNum; i++){
      var MessNum = 'Message' + i;
      var MessAttr = 'MessageAttr' + i;
      MessageFormGroups.push(
        <div key={i}>
          <ControlLabel>{MessNum}</ControlLabel>
          <FormGroup controlId={MessNum}>
            <Col componentClass={ControlLabel} sm={2}>
              {'body'}
            </Col>
            <Col sm={10}>
              <FormControl type="text" name={MessNum} value={this.state.MessNum} onChange={this.handleChange} placeholder={MessNum + ' body'} />
            </Col>
          </FormGroup>
          <FormGroup controlId="formControlsSelectMultiple">
            <ControlLabel>Select Attribute</ControlLabel>
            <FormControl componentClass="select" multiple name={MessAttr} value={this.state[MessAttr]} onChange={this.handleSelect} >
              {optionGroups}
            </FormControl>
          </FormGroup>
        </div>
      )
    }

    return (
      <Form horizontal id="add-message-form">
        <FormGroup controlId="formHorizontalName">
          <Col componentClass={ControlLabel} sm={2}>
            Message Set Name
          </Col>
          <Col sm={10}>
            <FormControl type="text" name='MessageSetName' value={this.state.MessageSetName} onChange={this.handleChange} placeholder="Message Set Name" />
          </Col>
        </FormGroup>
        <FormGroup controlId="formHorizontalAttrNum">
          <Col componentClass={ControlLabel} sm={2}>
            Number of Attributes
          </Col>
          <Col sm={10}>
            <FormControl type="number" name='AttrNum' value={this.state.AttrNum} onChange={this.handleChange} placeholder="Number of Attributes" />
          </Col>
        </FormGroup>
        {AttrFormGroups}
        <FormGroup controlId="formHorizontalText">
          <Col componentClass={ControlLabel} sm={2}>
           Number of Messages
          </Col>
          <Col sm={10}>
            <FormControl type="number" name='MessageNum' value={this.state.MessageNum} onChange={this.handleChange} placeholder="Number of Messages" />
          </Col>
        </FormGroup>
        {MessageFormGroups}
        <FormGroup>
          <Col smOffset={2} sm={10}>
            <Button type="submit" onClick={this.handleSubmit}>
                Create Message Set
            </Button>
          </Col>
        </FormGroup>
      </Form>
    );
  }
}

export default MessageSetForm;
