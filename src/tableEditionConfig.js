const config = {
	MESSAGES: {
		id: false,
		message_set: false,
		body_en: { type: 'textarea'},
		body_es: { type: 'textarea'},
		is_active: { type: 'checkbox', options: { values: 'true:false' }} ,
		attr_list: false
	},
	USERS: {
		created_time: false,
		phone: { type: 'number' },
		message_set: { type: 'select', options: { values: ['EBNHC', 'Text4Health', 'MASTERY'] } },
		time: { type: 'number' },
		send_message: { type: 'checkbox', options: { values: 'true:false' }} ,
		lang_code: { type: 'select', options: { values: ['en', 'es'] } },
		num_sent_messages: false,
		num_rated_messages: false,
		average_rating: false,
		preferred_attrs: { type: 'textarea'},
		is_real_user: { type: 'checkbox', options: { values: 'true:false' }},
		next_phone_call: { type: 'textarea'}
	}

}
export default config;