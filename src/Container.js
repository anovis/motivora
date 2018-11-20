import React, { Component } from 'react';
import {BootstrapTable, TableHeaderColumn} from 'react-bootstrap-table';
import PropTypes from 'prop-types';
import 'react-bootstrap-table/dist/react-bootstrap-table.min.css';
var axios = require('axios');


class Container extends Component {

    constructor (props) {
    super(props)
    this.state = {currentTab: 'responses' ,
    tableData : [],
    columns: ['phone','response','date']}
  }
 
  onClick(tab){
    this.setState({currentTab:tab});
    axios.get('https://5b36vt9t44.execute-api.us-east-1.amazonaws.com/api/' + tab)
    .then((response) => {
      this.setState({tableData: response.data.data})
    })
    .catch((error) => {console.log(error)})

    if(tab === 'responses'){
      this.setState({columns:['phone','response','date']});
    }
    else if(tab ==='users'){
      this.setState({columns:['phone','message_set','time','send_message','next_message']});
    }
    else{
        this.setState({columns:['id','message_set','body','total_sent','total_liked','total_disliked']});
    }

  }


  render() {
    return (
          <div>
            <Navbar currentTab={this.state.currentTab} onClick={this.onClick.bind(this)} />
            <Table tableData={this.state.tableData} columns={this.state.columns} />
        </div>
    );
  }
}



class BSTable extends React.Component {
  render() {
    var rowData = this.props.data;

    if (rowData) {
      var rows = [];
      var keys = Object.keys(rowData);
      var dataObject = {};
      dataObject['messages_sent'] = rowData['messages_sent'].length;
      rows.push(<TableHeaderColumn dataField='messages_sent' isKey={ true }>Messages Sent</TableHeaderColumn>);
      for (var i in keys){
        if (rowData[keys[i]]['attr'] === true){
          dataObject[keys[i]] = rowData[keys[i]]['beta'];
          rows.push(<TableHeaderColumn dataField={keys[i]}>{keys[i]}</TableHeaderColumn>);
        }
      }
      return (
        <BootstrapTable data={ [dataObject] }>
          {rows}
        </BootstrapTable>);
    } else {
      return (<p>?</p>);
    }
  }
}




class Table extends Component {
constructor (props) {
    super(props)
  }

    isExpandableRow(row) {
    if (row.next_message) return true;
    else return false;
  }

  expandComponent(row) {
    return (
      <BSTable data={ row } />
    );
  }


  render() {
    var col = this.props.columns;
    const options = {
      expandRowBgColor: 'rgb(249, 104, 104)'
    };
    if (this.props.columns.length ===6){
      return (
         <div>
              <BootstrapTable data={this.props.tableData} cellEdit={ cellEditProp } options={ options } keyField={ col[0] } striped hover>
             { col.map(name => <TableHeaderColumn dataField={ name } editable={ name==="body" ? true : false } dataSort={ true } filter={ { type: 'TextFilter', delay: 1000 } }>{ name }</TableHeaderColumn>) }
               </BootstrapTable>
            </div>
    );
    }
    else{
//             expandableRow={ this.isExpandableRow }  expandComponent={ this.expandComponent } removed
      return (
           <div>
                <BootstrapTable data={this.props.tableData} options={ options }  keyField={ col[0] } striped hover>
               { col.map(name => <TableHeaderColumn dataField={ name } dataSort={ true } filter={ { type: 'TextFilter', delay: 1000 } }>{ name }</TableHeaderColumn>) }
                 </BootstrapTable>
              </div>
      );
  }
  }
}

function onAfterSaveCell(row, cellName, cellValue) {
    axios.post('/editMessageBody', {
        row: row,
        cellValue: cellValue
      })
      .then(function (response) {
      })
      .catch(function (error) {
        console.log(error);
      });
}


const cellEditProp = {
  mode: 'dbclick',
  afterSaveCell: onAfterSaveCell  // a hook for after saving cell
};

class Navbar extends Component {
  constructor (props) {
    super(props)
  }


  render() {
    console.log(this.props.currentTab);
      var tabs = [];
      if (this.props.currentTab === 'responses'){
        tabs.push(<li role="presentation" onClick={() => { this.props.onClick('responses') }} className="active col-md-3"><a href="#">Responses</a></li>)
      }
      else{
        tabs.push(<li role="presentation" onClick={() => { this.props.onClick('responses') }} className=" col-md-3"><a href="#">Responses</a></li>)
      }
      if (this.props.currentTab === 'users'){
        tabs.push(<li role="presentation" onClick={() => { this.props.onClick('users') }} className="active col-md-3"><a href="#">Users</a></li>)
      }
      else{
        tabs.push(<li role="presentation" onClick={() => { this.props.onClick('users') }} className=" col-md-3"><a href="#">Users</a></li>)
      }
      if (this.props.currentTab === 'messages'){
        tabs.push(<li role="presentation" onClick={() => { this.props.onClick('messages') }} className="active col-md-3"><a href="#">Messages</a></li>)
      }
      else{
        tabs.push(<li role="presentation" onClick={() => { this.props.onClick('messages') }} className=" col-md-3"><a href="#">Messages</a></li>)
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


export default Container;