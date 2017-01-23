## Design
==========

PyQueuer is a Django based APP. It's built on Python 3.

### Authorization 

PyQueuer has a RBAC user system which is fully leverage Django ``User`` model.

Only 2 pages are created follow Django's _authorization guide_. These pages are build with Django _built-in forms_.

* Login page
* Register page

The templates are under **templates/registration/**. View names are **"login"** and **"register"**. We also need to configure **"urls.py"** by following the Django guide.

### Web UI

#### View & Templates

All views are function views in **views.py** currently. The templates are located in **templates** folder.

The web UI are built based on **JQuery UI** with its template. Many JQuery UI widgets are used in the pages.

A **base template** ``base.html`` is used as the base layout for all pages. It contains 4 **blocks** for convenience override in child pages.

* title block: To override the HTML page title (_title element_, text only)
* head block: To override the _Head element_ for additional meta, style or script.
* content block: To write real content of child pages.
* script block: To add additional scripts at the end of page so that will not impact page loading.

The following views are self-defined:

* index
* login
* register
* setting
* send
* consume
* plugin
* output

Some other views are referenced to _Django built-in views/forms_:

* logout
* admin
* password recover

#### Includes

#### Customer tags


### MQ module

MQ module defines all message queue (MQ) clients. It abstract the MQ client to a [some interfaces](#interfaces) (interfaces are actually base classes with some implementations).
 [``MQClientFactory``](#message-queue-client-factory) is provided to convenience creating instances. MQ types are defined in an enumerator class [``MQTyes``](#message-queue-types).

To use it, check the [usage examples](#usage)

#### Message Queue Types:

Now PyQueuer supports the following types.

* RabbitMQ: ``MQTypes.RabbitMQ`` (value "RabbitMQ") to identify. 
* Kafka: ``MQTypes.Kafka`` (value "Kafka") to identify.


#### Interfaces:

* ``IConnect``: respects a MQ client connection.
	* ``__init__``: Accepts an argument:
		*  ``conf``: A dict should contains all required parameters.
	* ``init``: _abstract method_. Child needs to implement it for own initialization logic. It will be called by ``__init__``.
	* ``auto_reconnect``: _property_. Flag to identify weather need to auto reconnect if lost connection.
	* ``config``: _property_. Stores the ``conf`` passed in from ``__init__``.
	* ``connect``: _abstract method_. To connect to a MQ (with given parameters ``config``)
	* ``disconnect``: _abstract method_. To disconnect from a MQ.
	* ``create_producer``: _abstract method_. Create and return an instance of **message producer** for this connection.
	* ``create_consumer``: _abstract method_. Create and return an instance of **message consumer** for this connection.

* ``IProduce``: abstract class respects a MQ producer.
	* ``__init__``: Accepts an argument
		*  conn: An connection to MQ (instance of **IConnect**).
	* ``connection``: _property_. Stores the ``conn`` passed in from ``__init__``.
	* ``basic_send``: _abstract method_. Low level method to send a message. Accepts arguments:
		* ``message``: _str_ or _json obj_. The message to be sent
		* ``kwargs``: _python keyword parameters_. To specify MQ required parameters.
	* ``produce``: _abstract method_. High level method to send a message.Accepts arguments:
		* ``message``: _str_ or _json obj_. The message to be sent
		* ``kwargs``: _python keyword parameters_. To specify MQ required parameters such as **"queue"**, **"topic"**, **"key"** and etc.

* ``IConsume``: abstract class respects a MQ consumer.
	* ``__init__``: Accepts an argument
		*  ``conn``: An connection to MQ (instance of ``IConnect``).
	* ``connection``: _property_. Stores the ``conn`` passed in from ``__init__``.
	* ``basic_get``: _abstract method_. Low level method to receive a message. Accepts arguments:
		* ``kwargs``: _python keyword parameters_. To specify MQ required parameters.
	* ``basic_ack``: _abstract method_. Low level method to acknowledge a message. Accepts arguments:
		* ``kwargs``: _python keyword parameters_. To specify MQ required parameters.
	* ``consume``: _abstract method_. High level method to receive messages. It should keep polling messages until being stopped. Accepts arguments:
		* ``kwargs``: _python keyword parameters_. To specify MQ required parameters such as **"queue"**, **"topic"**, **"key"** and etc. Also contains control parameters such as **"stop_event"** (python Event object to stop the consuming), **"callback"** (callback method to handle message. accepts one argument of message) and etc.

#### Message Queue client factory

* ``MQClientFactory``: factory class to create client instance.
	* ``__init__``: Accepts an argument
		* ``mq_type``: To specify the type of this client. (value of **MQType**)
	* ``create_connection``: _static method_. Create and return a connection based given arguments:
		* ``mq_type``: To specify the type of this client. (value of **MQType**)
		* ``conf``:  A dict should contains all required parameters. (Same as ``IConnect.__init__``)
	* ``create_producer``: _static method_. Create and return a MQ producer. (It calls ``IConnect.create_producer``.) Accepts arguments:
		* ``mq_type``: To specify the type of this client. (value of **MQType**)
		* ``conf``:  A dict should contains all required parameters. (Same as ``IConnect.__init__``)
	* ``create_consumer``: _static method_. Create and return a MQ consumer. (It calls ``IConnect.create_consumer``.) Accepts arguments:
		* ``mq_type``: To specify the type of this client. (value of **MQType**)
		* ``conf``:  A dict should contains all required parameters. (Same as ``IConnect.__init__``)
	* ``get_confs``: _static method_. To create an return a dict contains all required parameters for previous ``conf`` argument. The data are from ``Config`` model which were defined in ``setting`` page by user. Accepts arguments:
		* ``mq_type``: To specify the type of this client. (value of **MQType**)
		* ``user``: The user object respects current user. It could from ``request.user`` or ``User.objects.get`` and etc.
#### Usage

Basically you could use ``MQClientFactory`` to create a MQ client. Before that, you should implement the producer/consumer corresponding to specify MQ.

e.g. fast creation:

	conf = MQClientFactory.get_confs(mq_type=MQType.RabbitMQ, user=request.user)
	rabbit_producer = MQClientFactory.create_producer(mq_type=MQType.RabbitMQ, conf=conf)
	rabbit_producer.producer('Hello pyqueuer.', queue='my_app_incoming')

or from connection:

	user = User.objects.get(name='Jack')
	conf = MQClientFactory.get_confs(mq_type=MQType.RabbitMQ, user=request.user)
	conn = MQClientFactory.create_connection(mq_type=MQType.RabbitMQ, conf=conf)
	rabbit_producer = conn.create_producer()
	args = {
	  "topic": "all_logging",
	  "key": "warning"
	}
	rabbit_producer.producer('Hello pyqueuer.', **kwargs)


or consuming example:
	
	def on_msg(message):
	  print(message)
	event = threading.Event()
	conf = MQClientFactory.get_confs(mq_type=MQType.Kafka, user=request.user)
	kafka_consumer = MQClientFactory.creaet_consumer(mq_type=MQType.Kafka, conf=conf)
	kwargs = {
	  "queue": "sample",
	  "stop_event": event,
	  "callback": on_msg
	}
    print('Kafka consumer to queue "sample" is started.')
	kafka_consumer.consume(**kwargs)
	print('Kafka consumer to queue "sample" quit.')
	
	# in another thread/process to stop it.
	# The consumer.consume inplementation must check event.is_set().
	event.set()



### Plugin system (yapsy)
### Service
### Utilities
### Models
### Command Line
