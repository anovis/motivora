import React, { Component } from 'react';
import {BootstrapTable, TableHeaderColumn} from 'react-bootstrap-table';
import PropTypes from 'prop-types';
import 'react-bootstrap-table/dist/react-bootstrap-table.min.css';
import Config from './config';
import axios from 'axios';
import loader from './images/ajax-loader.gif';
import tableEditionConfig from './tableEditionConfig.js';


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
			USERS: {
				mode: 'dbclick',
				afterSaveCell: this.onAfterSaveUsersCell  // a hook for after saving cell
			},
			MESSAGES: {
				mode: 'dbclick',
				afterSaveCell: this.onAfterSaveMessagesCell  // a hook for after saving cell
			}
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
				this.setState({columns:['created_time', 'phone','message_set','time','send_message','lang_code', 'num_sent_messages', 'num_rated_messages']});
				endpoint = Config.api + '/users';
				break;
			case 'MESSAGES':
				this.setState({columns:['id','message_set','body_en','body_es','total_sent','total_liked','total_disliked', 'attr_list']});
				endpoint = Config.api + '/messages';
				break;
			default:
				console.error('No activePage supplied');
		}
		this.setState({loadingData: true});
		axios.get(endpoint)
			.then((response) => {
				console.log(response)
				this.setState({
					tableData: response.data.data,
					loadingData: false
				});
			})
			.catch((error) => {console.log(error)})
	}

	onAfterSaveMessagesCell(row, cellName, cellValue) {
		axios.put(Config.api + '/messages', {
			data:{
				id: row.id,
				message: row[cellName]
			}
		})
			.then(function (response) {console.log(response)})
			.catch(function (error) {
				console.log(error);
			});
	}
	onAfterSaveUsersCell(row, cellName, cellValue) {
		console.log(row, cellName, cellValue)
		let payload = {
			phone: row.phone
		};
		payload[cellName] = cellValue;
		axios.post(Config.api + '/user', payload)
			.then(function (response) {console.log(response)})
			.catch(function (error) {
				console.log(error);
			});
	}
	afterInsertRow(row) {
		console.log(row)
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

	render() {
		var col = this.state.columns;
		const options = {
			expandRowBgColor: 'rgb(249, 104, 104)',
			afterInsertRow: this.afterInsertRow
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
