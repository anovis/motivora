import React, { Component } from 'react';
import {BootstrapTable, TableHeaderColumn} from 'react-bootstrap-table';
import PropTypes from 'prop-types';
import 'react-bootstrap-table/dist/react-bootstrap-table.min.css';
import Config from './config';
import axios from 'axios';
import loader from './images/ajax-loader.gif';
import tableEditionConfig from './tableEditionConfig.js';
import { Link } from "react-router-dom";


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
			columns: ['phone','response','date']
		};
		this.cellEditProp = {
			USERS: {
				mode: 'dbclick',
				afterSaveCell: this.onAfterSaveUsersCell  // a hook for after saving cell
			},
			MESSAGES: {
				mode: 'dbclick',
				afterSaveCell: this.onAfterSaveMessagesCell  // a hook for after saving cell
			}
		};
		// This binding is necessary to make `this` work in the callback
		this.handleRowInsertion = this.handleRowInsertion.bind(this);
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
				this.setState({columns:['created_time', 'phone','message_set','average_rating', 'time','send_message','lang_code', 'num_sent_messages', 'num_rated_messages']});
				endpoint = Config.api + '/users';
				break;
			case 'MESSAGES':
				this.setState({columns:['id','message_set','body_en','body_es', 'is_active', 'attr_list']});
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

	onAfterSaveMessagesCell(row, cellName, cellValue) {
		let payload = {
			data:{
				id: row.id,
			}
		}
		payload['data'][cellName] = row[cellName];
		axios.put(Config.api + '/messages', payload)
			.then(function (response) {console.log('onAfterSaveMessagesCell', response)})
			.catch(function (error) {
				console.log(error);
			});
	}
	onAfterSaveUsersCell(row, cellName, cellValue) {
		let payload = {
			phone: row.phone
		};
		payload[cellName] = cellValue;
		axios.post(Config.api + '/user', payload)
			.then(function (response) {console.log('onAfterSaveUsersCell', response)})
			.catch(function (error) {
				console.log(error);
			});
	}
	handleRowInsertion(userData) {
		const _this = this;
		axios.post(Config.api + '/user', userData)
			.then(function (response) {
				if (response.status === 200) {
					_this.fetchData('USERS');
				}
			})
			.catch(function (error) {
				window.alert(error)
			});
	}

	isExpandableRow(row) {
		if (row.next_message) return true;
		else return false;
	}

	hasInsertRow() {
		if (this.props.activePage === 'USERS') {
			return true;
		} else {
			return false;
		}
	}
	getKeyField() {
		if (this.props.activePage === 'USERS') {
			return 'phone';
		} else {
			return 'id';
		}

	}
  	formatTimestamp(date) {
  		if (date) {
	  		let options = {month: 'long', year: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit', timeZone: "America/New_York"};
	  		return (new Date(date)).toLocaleDateString('en-US', options);
  		}
  	}

	getDataFormat(activePage, columnName) {
		let _this = this;
		return function(cell, row, enumObject, rowIndex) {
			if (activePage === 'USERS') {

				if (columnName === 'created_time') {
					
					var date = new Date(row[columnName]);
					return _this.formatTimestamp(date);

				} else if (columnName === 'phone') {

					return <Link to={`/user-details/${cell}`}>+{ cell }</Link>

				} else if (columnName === 'average_rating') {
					return <b>{ cell }</b>
				}
			} else if (activePage === 'MESSAGES') {

				if ((columnName === 'body_en') || (columnName === 'body_es')) {
					return <p style={ {whiteSpace: 'pre-wrap'}}>{ cell }</p>
				}
			}
			return cell;
		}
	}

	render() {
		var col = this.state.columns;
		const options = {
			expandRowBgColor: 'rgb(249, 104, 104)',
			onAddRow: this.handleRowInsertion
		};
		if (this.state.loadingData){
			return (
				<div className="ajax-loader-container">
					<img src={loader} alt="Loader"/>
				</div>
			);
		} else {
			return (
				<div>
					<BootstrapTable 
						data={ this.state.tableData } 
						cellEdit={ this.cellEditProp[this.props.activePage] } 
						insertRow={ this.hasInsertRow() }
						options={ options } 
						keyField={ col[0] } 
						exportCSV={ true }
						striped 
						hover
					>
						{col.map((name, idx) =>
							<TableHeaderColumn
								key={idx}
								dataField={ name }
								editable={ tableEditionConfig[this.props.activePage][name] }
								dataSort={ true }
								filter={ { type: 'TextFilter', delay: 1000 } }
								keyField={ this.getKeyField() }
								dataFormat={ this.getDataFormat(this.props.activePage, name).bind(this) }
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

Container.propTypes = {
	activePage: PropTypes.string.isRequired
}

Table.propTypes = {
	activePage: PropTypes.string.isRequired
}

export default Container;
