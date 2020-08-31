import React, { Component } from 'react';
import Config from './config';
import axios from 'axios';
import loader from './images/ajax-loader.gif';
import { CSVReader } from 'react-papaparse';
import { Form, Container, Col, Row, Button } from 'react-bootstrap';
import {BootstrapTable, TableHeaderColumn} from 'react-bootstrap-table';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faCheck, faTimes } from '@fortawesome/free-solid-svg-icons';


class CsvUploads extends Component {
	constructor(props) {
		super(props);
		this.state = {
			type: 'message_ratings',
			tableData: [],
			columns: [],
			uploading: false
		}
		this.handleOnDropCsvFile = this.handleOnDropCsvFile.bind(this);
		this.handleOnDropMessageRatingsCsvFile = this.handleOnDropMessageRatingsCsvFile.bind(this);
		this.handleOnDropMessagesCsvFile = this.handleOnDropMessagesCsvFile.bind(this);

		this.handleUploadTypeChange = this.handleUploadTypeChange.bind(this);
		this.handleOnRemoveCsvFile = this.handleOnRemoveCsvFile.bind(this);
		this.handleOnErrorCsvFile = this.handleOnErrorCsvFile.bind(this);

		this.upload = this.upload.bind(this);
		this.uploadMessageRatings = this.uploadMessageRatings.bind(this);
		this.uploadMessages = this.uploadMessages.bind(this);
	}
	handleOnDropCsvFile(data) {
		if (this.state.type === 'message_ratings') {
			
			this.handleOnDropMessageRatingsCsvFile(data);

		} else if (this.state.type === 'messages') {
			
			this.handleOnDropMessagesCsvFile(data);

		}

	}
	handleOnDropMessageRatingsCsvFile(data) {
		let ratings = [];
		let fields = ['phone', 'msg_id', 'rating']
		for (let i = 0; i < data.length; i++) {
			let row = data[i].data || {};
			let isFormatCorrect = true;
			for (let j = 0; j < fields.length; j++) {
				if (!(fields[j] in row)) {
					window.alert(`[Warning] Missing mandatory header ${fields[j]} for element ${i} `);
					isFormatCorrect = false;
					break;
				}
			}
			if (isFormatCorrect === true) {
				let elm = {};
				for (let j = 0; j < fields.length; j++) {
					elm[fields[j]] = row[fields[j]]
				}
				elm['sent_at'] = new Date();
				if (elm.phone) ratings.push(elm);
			}
		}
		this.setState({
			type: 'message_ratings',
			tableData: ratings,
			columns: ['phone', 'msg_id', 'rating']
		});
	}
	handleOnDropMessagesCsvFile(data) {
		let messages = [];
		let fields = ['message_set', 'id', 'is_active', 'body_en', 'body_es']
		for (let i = 0; i < data.length; i++) {
			let row = data[i].data || {};
			let attributes = [];
			let elm = {};
			for (let key in row) {
				if (fields.includes(key)) {
					elm[key] = row[key];
				} else {
					if (row[key] == 1) {
						attributes.push(key);
					}
				}
			}
			elm['attributes'] = attributes;
			if (elm.id) messages.push(elm);
		}
		this.setState({
			type: 'messages',
			tableData: messages,
			columns: ['uploaded', 'message_set', 'id', 'is_active', 'body_en', 'body_es', 'attributes']
		});
	}

	handleOnErrorCsvFile(err, file, inputElem, reason) {
		window.alert(err);
	}

	handleOnRemoveCsvFile(data) {
		this.setState({
			tableData: [],
			columns: []
		});
	}
	handleUploadTypeChange(event) {
    	const target = event.target;
    	const value = target.value;
    	const name = target.name;
    	this.setState({type: value})
	}
	async upload(event) {
		this.setState({uploading: true});
		if (this.state.type === 'message_ratings') {
			
			this.uploadMessageRatings();

		} else if (this.state.type === 'messages') {
			const CHUNK_SIZE = 50;
			//1) split the messages into chunks and make sure to make a copy of that (not a reference)
			let chunks = JSON.parse(JSON.stringify(_chunkArray(this.state.tableData, CHUNK_SIZE)));
			for (let i = 0; i < chunks.length; i++) {
				let chunk = chunks[i];
				let _this = this;
				await this.uploadMessages(chunk)
					.then(function() {
						//Remove uploaded messages from the tableData
						for (let j = 0; j < chunk.length; j++) {
							let message = chunk[j];
							let index = i * CHUNK_SIZE + j;
							_this.state.tableData[index].uploaded = true;
						}
					})
					.catch(error => {
	        			window.alert(error);
						for (let j = 0; j < chunk.length; j++) {
							let message = chunk[j];
							let index = i * CHUNK_SIZE + j;
							_this.state.tableData[index].uploaded = false;
						}
						
					})
				this.setState({tableData: this.state.tableData});
			}
		}
		this.setState({uploading: false});
	}

	uploadMessageRatings() {
		console.log('uploadMessageRatings')

	    const _this = this;
	    axios.post(Config.api + '/users/add_message_rating', {
	        message_ratings: this.state.tableData
	    })
	    .then(response => {
	    	if (response && response.status === 200) {
	        	window.alert('Ratings added successfully')
	    	} else {
	        	window.alert('An error occured on the server. Please contact the admin');
	    	}
	    })
	    .catch(error => {
	        window.alert('An error occured on the server. Please contact the admin');
	    });
	}
	
	uploadMessages(messages) {
		return new Promise(function(resolve, reject) {
		    const _this = this;
		    axios.post(Config.api + '/messages', {
		        messages: messages
		    })
		    .then(response => {
		    	if (response && response.status === 200) {
		        	resolve(true);
		    	} else {
		        	reject('An error occured on the server. Please contact the admin');
		    	}
		    })
		    .catch(error => {
		        reject(error);
		    });
		})


	}

	getWarning() {
		if (this.state.type === 'message_ratings') {
			return 'Expected headers: phone, message_id, rating'
		} else if (this.state.type === 'messages') {
			return 'Expected headers: message_set, id, is_active, body_en, body_es (AND any column other than the previous ones is considered to be an attribute - put 1 if attribute if present or 0 if not)'
		}
	}
	getDataFormat(columnName) {
		return function(cell, row, enumObject, rowIndex) {
			if (columnName === 'uploaded') {
				if (cell == true) {
					
					return <FontAwesomeIcon icon={faCheck} size="lg" style={{ color: 'green' }}/>;

				} else if (cell == false) {

					return <FontAwesomeIcon icon={faTimes} size="lg" style={{ color: 'red' }}/>;
					
				} else {
					return cell;
				}
			}
			return cell;
		}
	}
	render() {
		var columns = this.state.columns || [];
		return (
			<div>
				<Container style={{ paddingTop: '20px' }}>
					<Row>

						<Col xs={4}>
							<Form>
			  					<Form.Group>
			    					<Form.Label>Upload type</Form.Label>
									<Form.Control as="select" onChange={this.handleUploadTypeChange}>
			  							<option value="message_ratings">Message ratings</option>
			  							<option value="messages">Messages</option>
			  						</Form.Control>
			  					</Form.Group>
			  					{
			  						(this.state.tableData.length > 0)
			  							?
									<button type="button" className="btn btn-success" onClick={this.upload}>
            							Upload data
          							</button>
			  							:
			  						null
			  					}
			  					{
			  						(this.state.uploading)
			  							?
			  						<div className="ajax-loader-container">
										<img src={loader} alt="Loader"/>
									</div>
										:
									null
			  					}
			  				</Form>
						</Col>
						<Col xs={8}>
							<div 
								role="alert" 
								className="alert alert-warning"
							>{ this.getWarning() }</div>
							<CSVReader
								onDrop={this.handleOnDropCsvFile}
								onError={this.handleOnErrorCsvFile}
								addRemoveButton
								onRemoveFile={this.handleOnRemoveCsvFile}
								config={{
									header: true,
								}}
							>
								<span>Drop CSV file here or click to add message ratings.</span>
							</CSVReader>
						</Col>
					</Row>
					<Row>
						{ 
							(columns.length > 0)
								?
							<BootstrapTable 
								data={ this.state.tableData } 
								keyField={ columns[0] } 
								striped 
								hover
							>
								{columns.map((name, idx) =>
									<TableHeaderColumn
										key={idx}
										dataField={ name }
										dataSort={ true }
										filter={ { type: 'TextFilter', delay: 1000 } }
										dataFormat={ this.getDataFormat(name).bind(this) }
									>
										{ name }
									</TableHeaderColumn>
								)}
							</BootstrapTable>
								:
							null
						}
					</Row>
				</Container>
			</div>
		)
	}
}
function _chunkArray(arr, chunkSize) {
	var result = [];
	if (arr && Array.isArray(arr)) {
		for (var i = 0; i < arr.length; i += chunkSize) {
	  		result.push(arr.slice(i, i + chunkSize));
		}
	}
	return result;
}
export default CsvUploads;