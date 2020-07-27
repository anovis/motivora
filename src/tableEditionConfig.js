const config = {
	MESSAGES: {
		id: false,
		message_set: false,
		body: { type: 'textarea'},
		total_sent: false,
		total_liked: false,
		total_disliked: false,
		attr_list: false
	},
	USERS: {
		phone: false,
		message_set: { type: 'select', options: { values: ['EBNHC'] } },
		time: { type: 'number' },
		send_message: { type: 'checkbox', options: { values: 'true:false' }} ,
		lang_code: { type: 'select', options: { values: ['en', 'es'] } }
	}

}
export default config;