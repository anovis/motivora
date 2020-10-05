import React, { Component } from 'react';
import {BootstrapTable, TableHeaderColumn} from 'react-bootstrap-table';
import PropTypes from 'prop-types';
import 'react-bootstrap-table/dist/react-bootstrap-table.min.css';
import Config from './config';
import axios from 'axios';
import loader from './images/ajax-loader.gif';
import tableEditionConfig from './tableEditionConfig.js';
import { Link } from "react-router-dom";
import MessageDetails from './MessageDetails';
import { Form, Container, Col, Row, Badge } from 'react-bootstrap';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faCheck, faTimes } from '@fortawesome/free-solid-svg-icons';


class PageContainer extends Component {

	constructor (props) {
		super(props);
		this.state = {
			messageSet: 'EBNHC'
		};
		this.handleMessageSetChange = this.handleMessageSetChange.bind(this);
	}
	handleMessageSetChange(event) {
    	const target = event.target;
    	const value = target.value;
    	const name = target.name;
    	this.setState({messageSet: value})
	}


	render() {
		return (
			<div>
				<hr/>
				<Container>
					<Row>
						<Col xs={{ span: 4, offset: 4 }}>
							<Form>
			  					<Form.Group>
			    					<Form.Label>Study</Form.Label>
									<Form.Control as="select" onChange={this.handleMessageSetChange}>
			  							<option>EBNHC</option>
			  							<option>Text4Health</option>
			  							<option>MASTERY</option>
			  						</Form.Control>
			  					</Form.Group>
			  				</Form>
			  			</Col>
			  		</Row>
				</Container>
				<hr/>
				<Table activePage={this.props.activePage} messageSet={this.state.messageSet}/>
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
			expanding: []
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
		this.isExpandableRow = this.isExpandableRow.bind(this);
		this.expandRow = this.expandRow.bind(this);
		this.expandComponent = this.expandComponent.bind(this);
		
	}

	componentDidMount() {
		this.fetchData(this.props.activePage, this.props.messageSet);
	}

	componentWillReceiveProps(nextProps) {
		if ((this.props.activePage !== nextProps.activePage) || (this.props.messageSet !== nextProps.messageSet)) {
			this.fetchData(nextProps.activePage, nextProps.messageSet);
		}
	}

	fetchData(activePage, messageSet) {
		let endpoint;
		switch(activePage){
			case'RESPONSES':
				this.setState({columns:['phone','response','date']});
				endpoint = Config.api + '/responses';
				break;
			case'USERS':
				this.setState({columns:['created_time', 'phone','message_set','average_rating', 'time','send_message','lang_code', 'num_sent_messages', 'num_rated_messages', 'is_real_user', 'preferred_attrs']});
				endpoint = Config.api + '/users';
				break;
			case 'MESSAGES':
				this.setState({columns:['id','message_set','body_en','body_es', 'is_active', 'total_sent', 'total_rated', 'average_rating', 'attr_list']});
				endpoint = Config.api + '/messages';
				break;
			default:
				console.error('No activePage supplied');
		}
		this.setState({loadingData: true});
		let params = {
			message_set: messageSet
		}
		axios.get(endpoint, {params: params})
			.then((response) => {
				this.setState({
					tableData: response.data.data,
					loadingData: false
				});
			})
			.catch((error) => {
				window.alert(error)
				this.setState({
					loadingData: false,
				});
			})
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
		if ((cellName === 'preferred_attrs') && cellValue) {
			payload[cellName] = cellValue.split(",");
		} else {
			payload[cellName] = cellValue;
		}
		axios.post(Config.api + '/user', payload)
			.then(function (response) {console.log('onAfterSaveUsersCell', response)})
			.catch(function (error) {
				console.log(error);
			});
	}
	handleRowInsertion(userData) {
		const _this = this;
		if (userData.preferred_attrs) {
			userData.preferred_attrs = userData.preferred_attrs.split(",");
		}
		axios.post(Config.api + '/user', userData)
			.then(function (response) {
				if (response.status === 200) {
					_this.fetchData('USERS', userData.message_set || 'EBNHC');
				}
			})
			.catch(function (error) {
				window.alert(error)
			});
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
	
	isExpandableRow(row) {
		if (this.props.activePage === 'MESSAGES') {
			return true;
		} else {
			return false;
		}

	}
  	expandRow(rowId) {
  		let _this = this;
  		return function(event) {
  			if (_this.state.expanding.indexOf(rowId) > -1) {
  				_this.setState({expanding: []});
  			} else {
  				_this.setState({expanding: [rowId]});
  			}
  			event.preventDefault();
  		}
  	}
	expandComponent(row) {
  		let _this = this;
		return ((_this.state.expanding.indexOf(row.id) > -1) ? <MessageDetails message={ row } /> : null)
	}

	getDataFormat(activePage, columnName) {
		let _this = this;
		return function(cell, row, enumObject, rowIndex) {
			if (activePage === 'USERS') {

				if (columnName === 'created_time') {
					
					var date = new Date(row[columnName]);
					return _this.formatTimestamp(date);

				} else if (columnName === 'phone') {

					return <Link to={`/user-details/${cell}`}>+{ cell }</Link>;

				} else if (columnName === 'average_rating') {
					
					return <b>{ cell }</b>;

				} else if ((columnName === 'send_message') || (columnName === 'is_real_user')) {
					if (cell == true) {
						
						return <FontAwesomeIcon icon={faCheck} size="lg" style={{ color: 'green' }}/>;

					} else if (cell == false) {

						return <FontAwesomeIcon icon={faTimes} size="lg" style={{ color: 'red' }}/>;
						
					} else {
						return cell;
					}
				} else if (columnName === 'preferred_attrs') {
					if (cell) {
						if (!Array.isArray(cell)) {
							cell = cell.split(",");
						}
						return (
							<div style={ {whiteSpace: 'pre-wrap'}}>
								{ cell.map((attr, index) => <span><Badge key={ index} variant="primary">{ attr }</Badge>{ ' '}</span>) }
							</div>
						)
					}

				}
			} else if (activePage === 'MESSAGES') {

				if ((columnName === 'body_en') || (columnName === 'body_es')) {
					
					return <p style={ {whiteSpace: 'pre-wrap'}}>{ cell }</p>;

				} else if (columnName === 'id') {

					return <a href="#" onClick={ this.expandRow(cell) }>#{ cell } Click to see details</a>;

				} else if (columnName === 'attr_list') {
					if (cell) {
						try {
							cell = cell.replace(/\'/g, '"');
							cell = cell.replace(/True/g, 'true');
							cell = cell.replace(/False/g, 'false');
							let attrsDict = JSON.parse(cell)
							return (
								<div style={ {whiteSpace: 'pre-wrap'}}>
									{ Object.keys(attrsDict).map((attr, index) => (attrsDict[attr] === true) ? <span><Badge key={ index} variant="primary">{ attr }</Badge>{ ' '}</span> : null) }
								</div>
							);

						} catch (e) {
							console.log(e)
							return 'Error while parsing the cell data'
						}
					}

				}
			}
			return cell;
		}
	}

	render() {
		var col = this.state.columns;
		const options = {
			expandRowBgColor: '#ffffff',
			onAddRow: this.handleRowInsertion,
			expanding: this.state.expanding
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
						expandableRow={ this.isExpandableRow }
        				expandComponent={ this.expandComponent }
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

PageContainer.propTypes = {
	activePage: PropTypes.string.isRequired
}

Table.propTypes = {
	activePage: PropTypes.string.isRequired
}

export default PageContainer;
