const config = {
	MESSAGES: {
		id: false,
		message_set: false,
		body_en: { type: 'textarea'},
		body_es: { type: 'textarea'},
		attr_list: false
	},
	USERS: {
		created_time: false,
		phone: { type: 'number' },
		message_set: { type: 'select', options: { values: ['EBNHC'] } },
		time: { type: 'number' },
		send_message: { type: 'checkbox', options: { values: 'true:false' }} ,
		lang_code: { type: 'select', options: { values: ['en', 'es'] } },
		num_sent_messages: false,
		num_rated_messages: false,
	}

}
export default config;