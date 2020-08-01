import React, { Component } from 'react';
import Config from './config';
import axios from 'axios';
import loader from './images/ajax-loader.gif';
import { CSVReader } from 'react-papaparse';
import { Container, Col, Row } from 'react-bootstrap';


class CsvUploads extends Component {
	constructor(props) {
		super(props);
	}
	handleOnDropCsvFile(data) {
		let ratings = [];
		for (let i = 0; i < data.length; i++) {
			let row = data[i].data || {};
			if (!('phone' in row) || !('message_id' in row) || !('rating' in row)) {
				window.alert(`Missing mandatory header for element ${i} `);
				return
			}
			let isNewPhone = true;
			for (let j = 0; j < ratings.length; j++) {
				let rating = ratings[j];
				if (rating.phone == row.phone) {
					rating.message_ratings.push({
						sent_at: new Date(),
						msg_id: parseInt(row.message_id),
    					rating: parseInt(row.rating)
    				});
					isNewPhone = false;
					break;
				}
			}
			if (isNewPhone === true) {
				if (row.phone) {
					ratings.push({
						phone: row.phone,
						message_ratings: [{
							sent_at: new Date(),
							msg_id: parseInt(row.message_id),
	    					rating: parseInt(row.rating)
	    				}]
					});
				}
			}
		}
		console.log(ratings)
	}

	handleOnErrorCsvFile(err, file, inputElem, reason) {
		window.alert(err);
	}

	handleOnRemoveCsvFile(data) {
		console.log('---------------------------')
		console.log(data)
		console.log('---------------------------')
	}
	render() {
		return (
			<div>
				<Container style={{ paddingBottom: '20px' }}>
					<Row>
						<Col xs={4}>
							<p>Expected headers: phone, message_id, rating</p>
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
				</Container>
			</div>
		)
	}
}

export default CsvUploads;