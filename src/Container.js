import React, { Component } from 'react';
import {BootstrapTable, TableHeaderColumn} from 'react-bootstrap-table';
import PropTypes from 'prop-types';
import 'react-bootstrap-table/dist/react-bootstrap-table.min.css';
import Config from './config';
import axios from 'axios';
import loader from './images/ajax-loader.gif';

class Container extends Component {

  constructor (props) {
    super(props);
    this.state = {};
  }

  render() {
    return (
      <div>
        <Table activePage={this.props.activePage}/>
      </div>
    );
  }
}

class Table extends Component {

  constructor (props) {
    super(props)
    this.state = {
      tableData: [],
      columns: ['phone','response','date'],
    };
    this.cellEditProp = {
      mode: 'dbclick',
      afterSaveCell: this.onAfterSaveCell  // a hook for after saving cell
    };
  }

  componentDidMount() {
    this.fetchData(this.props.activePage);
  }

  componentWillReceiveProps(nextProps) {
    // Active page changing
    if(this.props.activePage !== nextProps.activePage) {
      this.fetchData(nextProps.activePage);
    }
  }

  fetchData(activePage) {
    let endpoint;
    switch(activePage){
      case'RESPONSES':
        this.setState({columns:['phone','response','date']});
        endpoint = Config.api + '/responses';
        break;
      case'USERS':
        this.setState({columns:['phone','message_set','time','send_message','next_message']});
        endpoint = Config.api + '/users';
        break;
      case 'MESSAGES':
        this.setState({columns:['id','message_set','body','total_sent','total_liked','total_disliked']});
        endpoint = Config.api + '/messages';
        break;
      default:
        console.error('No activePage supplied');
    }
    this.setState({loadingData: true});
    axios.get(endpoint)
      .then((response) => {
        this.setState({
          tableData: response.data.data,
          loadingData: false
        });
      })
      .catch((error) => {console.log(error)})
  }

  onAfterSaveCell(row, cellName, cellValue) {
    axios.patch(Config.api + '/messages', {
      data:{
        id: row.id,
        message: row.body
      }
    })
    .then(function (response) {
    })
    .catch(function (error) {
      console.log(error);
    });
  }

  isExpandableRow(row) {
    if (row.next_message) return true;
    else return false;
  }

  render() {
    var col = this.state.columns;
    const options = {
      expandRowBgColor: 'rgb(249, 104, 104)'
    };
    if(this.state.loadingData){
      return (
        <div className="ajax-loader-container">
          <img src={loader} alt="Loader"/>
        </div>
      );
    }
    else{
      if (this.state.columns.length === 6){
        return (
          <div>
            <BootstrapTable data={ this.state.tableData } cellEdit={ this.cellEditProp } options={ options } keyField={ col[0] } striped hover>
              {col.map((name, idx) =>
                <TableHeaderColumn
                  key={idx}
                  dataField={ name }
                  editable={ name==="body" ? true : false }
                  dataSort={ true }
                  filter={ { type: 'TextFilter', delay: 1000 } }
                >
                  { name }
                </TableHeaderColumn>
              )}
            </BootstrapTable>
          </div>
        );
      }
      else{
        return (
          <div>
            <BootstrapTable data={ this.state.tableData } options={ options }  keyField={ col[0] } striped hover>
              {col.map((name, idx) =>
                <TableHeaderColumn
                  key={idx}
                  dataField={ name }
                  dataSort={ true }
                  filter={ { type: 'TextFilter', delay: 1000 } }
                >
                  { name }
                </TableHeaderColumn>
              )}
             </BootstrapTable>
          </div>
        );
      }
    }
  }
}

Container.propTypes = {
  activePage: PropTypes.string.isRequired
}

Table.propTypes = {
  activePage: PropTypes.string.isRequired
}

export default Container;
