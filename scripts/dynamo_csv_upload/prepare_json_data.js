const fs = require('fs')
const parse = require('csv-parse/lib/sync')
const _ = require('lodash');

const contents = fs.readFileSync('./raw_data.csv', 'utf-8')
const data = parse(contents, {columns: true})

const parseAttributes = object => {
  const attributes = _.keys(object);
  _.remove(attributes, key => key === 'body');
  let finalObj = {};
  let count = 0;
  for(let i = 0, l = attributes.length; i < l; i++){
    const attr = attributes[i];
    if(parseInt(object[attr]) === 0) continue;
    finalObj[attr] = {"BOOL": true};
    count++;
  }
  return {
    object: finalObj,
    size: count
  };
}

// Set this value to be the current highest ID of the messages in the table.
const currentHighestId = 0;
const finalData = data.map( (obj, idx) => {
  const attributes = parseAttributes(obj);
  return {
    "PutRequest": {
      "Item": {
        "id": {
          "N": `${currentHighestId + idx + 1}`
        },
        "body": {
          "S": obj.body
        },
        "message_set": {
          "S": "EBNHC"
        },
        "seq": {
          "N": `${currentHighestId + idx + 1}`
        },
        "total_attr": {
          "N": `${attributes.size}`
        },
        "attr_list": {
          "M": attributes.object
        },
        "total_disliked": {
          "N": "0"
        },
        "total_liked": {
          "N": "0"
        },
        "total_resp": {
          "N": "0"
        },
        "total_sent": {
          "N": "0"
        }
      }
    }
  }
});

// Break data into chunks of 25 put requests
// AWS has an abitrary limit: https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_BatchWriteItem.html
const dataChunks = _.chunk(finalData, 25);
_.each(dataChunks, (chunk, idx) => {
  fs.writeFile(`./data_to_upload/data-${idx}.json`, JSON.stringify({
    "motivora-messages": chunk
  }), err => {
    if(err) {
      return console.log(err);
    }
    console.log("The file was saved!");
  });
});

