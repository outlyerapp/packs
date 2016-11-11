#!/usr/bin/env python

"""
    Kafka Plugin - Monitors Kafka process via JMX
"""

import subprocess
import json

# Path to Java binary. On Windows, you should use forward slashes as the path separator
JAVA_BIN = "java"

# Set the JMX URL Endpoint to Connect To
JMX_URL = 'service:jmx:rmi:///jndi/rmi://localhost:55555/jmxrmi'

# Set JMX Username, if authentication required
JMX_USERNAME = ''

# Set JMX Password, if authentication required
JMX_PASSWORD = ''

# Define query of metrics you wish to pull with output names as they will appear in Dataloop when you browse metrics

METRICS = "kafka.server.delayedproducerrequestmetrics.expirespersecond.count=kafka.server:type=DelayedProducerRequestMetrics,name=ExpiresPerSecond/Count;" + \
          "kafka.server.delayedproducerrequestmetrics.expirespersecond.eventtype=kafka.server:type=DelayedProducerRequestMetrics,name=ExpiresPerSecond/EventType;" + \
          "kafka.server.delayedproducerrequestmetrics.expirespersecond.rateunit=kafka.server:type=DelayedProducerRequestMetrics,name=ExpiresPerSecond/RateUnit;" + \
          "kafka.server.delayedproducerrequestmetrics.expirespersecond.meanrate=kafka.server:type=DelayedProducerRequestMetrics,name=ExpiresPerSecond/MeanRate;" + \
          "kafka.server.delayedproducerrequestmetrics.expirespersecond.oneminuterate=kafka.server:type=DelayedProducerRequestMetrics,name=ExpiresPerSecond/OneMinuteRate;" + \
          "kafka.server.delayedproducerrequestmetrics.expirespersecond.fiveminuterate=kafka.server:type=DelayedProducerRequestMetrics,name=ExpiresPerSecond/FiveMinuteRate;" + \
          "kafka.server.delayedproducerrequestmetrics.expirespersecond.fifteenminuterate=kafka.server:type=DelayedProducerRequestMetrics,name=ExpiresPerSecond/FifteenMinuteRate;" + \
          "kafka.server.producerrequestpurgatory.purgatorysize.value=kafka.server:type=ProducerRequestPurgatory,name=PurgatorySize/Value;" + \
          "kafka.server.brokertopicmetrics.bytesrejectedpersec.count=kafka.server:type=BrokerTopicMetrics,name=BytesRejectedPerSec/Count;" + \
          "kafka.server.brokertopicmetrics.bytesrejectedpersec.eventtype=kafka.server:type=BrokerTopicMetrics,name=BytesRejectedPerSec/EventType;" + \
          "kafka.server.brokertopicmetrics.bytesrejectedpersec.rateunit=kafka.server:type=BrokerTopicMetrics,name=BytesRejectedPerSec/RateUnit;" + \
          "kafka.server.brokertopicmetrics.bytesrejectedpersec.meanrate=kafka.server:type=BrokerTopicMetrics,name=BytesRejectedPerSec/MeanRate;" + \
          "kafka.server.brokertopicmetrics.bytesrejectedpersec.oneminuterate=kafka.server:type=BrokerTopicMetrics,name=BytesRejectedPerSec/OneMinuteRate;" + \
          "kafka.server.brokertopicmetrics.bytesrejectedpersec.fiveminuterate=kafka.server:type=BrokerTopicMetrics,name=BytesRejectedPerSec/FiveMinuteRate;" + \
          "kafka.server.brokertopicmetrics.bytesrejectedpersec.fifteenminuterate=kafka.server:type=BrokerTopicMetrics,name=BytesRejectedPerSec/FifteenMinuteRate;" + \
          "kafka.network.requestchannel.responsequeuesize.value=kafka.network:type=RequestChannel,name=ResponseQueueSize/Value;" + \
          "kafka.network.socketserver.idlepercent.networkprocessor.1.count=kafka.network:type=SocketServer,name=IdlePercent,networkProcessor=1/Count;" + \
          "kafka.network.socketserver.idlepercent.networkprocessor.1.eventtype=kafka.network:type=SocketServer,name=IdlePercent,networkProcessor=1/EventType;" + \
          "kafka.network.socketserver.idlepercent.networkprocessor.1.rateunit=kafka.network:type=SocketServer,name=IdlePercent,networkProcessor=1/RateUnit;" + \
          "kafka.network.socketserver.idlepercent.networkprocessor.1.meanrate=kafka.network:type=SocketServer,name=IdlePercent,networkProcessor=1/MeanRate;" + \
          "kafka.network.socketserver.idlepercent.networkprocessor.1.oneminuterate=kafka.network:type=SocketServer,name=IdlePercent,networkProcessor=1/OneMinuteRate;" + \
          "kafka.network.socketserver.idlepercent.networkprocessor.1.fiveminuterate=kafka.network:type=SocketServer,name=IdlePercent,networkProcessor=1/FiveMinuteRate;" + \
          "kafka.network.socketserver.idlepercent.networkprocessor.1.fifteenminuterate=kafka.network:type=SocketServer,name=IdlePercent,networkProcessor=1/FifteenMinuteRate;" + \
          "kafka.server.offsetmanager.numoffsets.value=kafka.server:type=OffsetManager,name=NumOffsets/Value;" + \
          "kafka.network.requestchannel.responsequeuesize.processor.0.value=kafka.network:type=RequestChannel,name=ResponseQueueSize,processor=0/Value;" + \
          "kafka.server.kafkaserver.brokerstate.value=kafka.server:type=KafkaServer,name=BrokerState/Value;" + \
          "kafka.controller.kafkacontroller.offlinepartitionscount.value=kafka.controller:type=KafkaController,name=OfflinePartitionsCount/Value;" + \
          "kafka.server.kafkarequesthandlerpool.requesthandleravgidlepercent.count=kafka.server:type=KafkaRequestHandlerPool,name=RequestHandlerAvgIdlePercent/Count;" + \
          "kafka.server.kafkarequesthandlerpool.requesthandleravgidlepercent.eventtype=kafka.server:type=KafkaRequestHandlerPool,name=RequestHandlerAvgIdlePercent/EventType;" + \
          "kafka.server.kafkarequesthandlerpool.requesthandleravgidlepercent.rateunit=kafka.server:type=KafkaRequestHandlerPool,name=RequestHandlerAvgIdlePercent/RateUnit;" + \
          "kafka.server.kafkarequesthandlerpool.requesthandleravgidlepercent.meanrate=kafka.server:type=KafkaRequestHandlerPool,name=RequestHandlerAvgIdlePercent/MeanRate;" + \
          "kafka.server.kafkarequesthandlerpool.requesthandleravgidlepercent.oneminuterate=kafka.server:type=KafkaRequestHandlerPool,name=RequestHandlerAvgIdlePercent/OneMinuteRate;" + \
          "kafka.server.kafkarequesthandlerpool.requesthandleravgidlepercent.fiveminuterate=kafka.server:type=KafkaRequestHandlerPool,name=RequestHandlerAvgIdlePercent/FiveMinuteRate;" + \
          "kafka.server.kafkarequesthandlerpool.requesthandleravgidlepercent.fifteenminuterate=kafka.server:type=KafkaRequestHandlerPool,name=RequestHandlerAvgIdlePercent/FifteenMinuteRate;" + \
          "kafka.network.socketserver.idlepercent.networkprocessor.0.count=kafka.network:type=SocketServer,name=IdlePercent,networkProcessor=0/Count;" + \
          "kafka.network.socketserver.idlepercent.networkprocessor.0.eventtype=kafka.network:type=SocketServer,name=IdlePercent,networkProcessor=0/EventType;" + \
          "kafka.network.socketserver.idlepercent.networkprocessor.0.rateunit=kafka.network:type=SocketServer,name=IdlePercent,networkProcessor=0/RateUnit;" + \
          "kafka.network.socketserver.idlepercent.networkprocessor.0.meanrate=kafka.network:type=SocketServer,name=IdlePercent,networkProcessor=0/MeanRate;" + \
          "kafka.network.socketserver.idlepercent.networkprocessor.0.oneminuterate=kafka.network:type=SocketServer,name=IdlePercent,networkProcessor=0/OneMinuteRate;" + \
          "kafka.network.socketserver.idlepercent.networkprocessor.0.fiveminuterate=kafka.network:type=SocketServer,name=IdlePercent,networkProcessor=0/FiveMinuteRate;" + \
          "kafka.network.socketserver.idlepercent.networkprocessor.0.fifteenminuterate=kafka.network:type=SocketServer,name=IdlePercent,networkProcessor=0/FifteenMinuteRate;" + \
          "kafka.common.appinfo.version.value=kafka.common:type=AppInfo,name=Version/Value;" + \
          "kafka.network.requestchannel.requestqueuesize.value=kafka.network:type=RequestChannel,name=RequestQueueSize/Value;" + \
          "kafka.server.replicafetchermanager.maxlag.clientid.replica.value=kafka.server:type=ReplicaFetcherManager,name=MaxLag,clientId=Replica/Value;" + \
          "kafka.server.fetchrequestpurgatory.numdelayedrequests.value=kafka.server:type=FetchRequestPurgatory,name=NumDelayedRequests/Value;" + \
          "kafka.server.replicafetchermanager.minfetchrate.clientid.replica.value=kafka.server:type=ReplicaFetcherManager,name=MinFetchRate,clientId=Replica/Value;" + \
          "kafka.server.fetchrequestpurgatory.purgatorysize.value=kafka.server:type=FetchRequestPurgatory,name=PurgatorySize/Value;" + \
          "kafka.controller.kafkacontroller.preferredreplicaimbalancecount.value=kafka.controller:type=KafkaController,name=PreferredReplicaImbalanceCount/Value;" + \
          "kafka.server.brokertopicmetrics.bytesoutpersec.count=kafka.server:type=BrokerTopicMetrics,name=BytesOutPerSec/Count;" + \
          "kafka.server.brokertopicmetrics.bytesoutpersec.eventtype=kafka.server:type=BrokerTopicMetrics,name=BytesOutPerSec/EventType;" + \
          "kafka.server.brokertopicmetrics.bytesoutpersec.rateunit=kafka.server:type=BrokerTopicMetrics,name=BytesOutPerSec/RateUnit;" + \
          "kafka.server.brokertopicmetrics.bytesoutpersec.meanrate=kafka.server:type=BrokerTopicMetrics,name=BytesOutPerSec/MeanRate;" + \
          "kafka.server.brokertopicmetrics.bytesoutpersec.oneminuterate=kafka.server:type=BrokerTopicMetrics,name=BytesOutPerSec/OneMinuteRate;" + \
          "kafka.server.brokertopicmetrics.bytesoutpersec.fiveminuterate=kafka.server:type=BrokerTopicMetrics,name=BytesOutPerSec/FiveMinuteRate;" + \
          "kafka.server.brokertopicmetrics.bytesoutpersec.fifteenminuterate=kafka.server:type=BrokerTopicMetrics,name=BytesOutPerSec/FifteenMinuteRate;" + \
          "kafka.network.socketserver.networkprocessoravgidlepercent.count=kafka.network:type=SocketServer,name=NetworkProcessorAvgIdlePercent/Count;" + \
          "kafka.network.socketserver.networkprocessoravgidlepercent.eventtype=kafka.network:type=SocketServer,name=NetworkProcessorAvgIdlePercent/EventType;" + \
          "kafka.network.socketserver.networkprocessoravgidlepercent.rateunit=kafka.network:type=SocketServer,name=NetworkProcessorAvgIdlePercent/RateUnit;" + \
          "kafka.network.socketserver.networkprocessoravgidlepercent.meanrate=kafka.network:type=SocketServer,name=NetworkProcessorAvgIdlePercent/MeanRate;" + \
          "kafka.network.socketserver.networkprocessoravgidlepercent.oneminuterate=kafka.network:type=SocketServer,name=NetworkProcessorAvgIdlePercent/OneMinuteRate;" + \
          "kafka.network.socketserver.networkprocessoravgidlepercent.fiveminuterate=kafka.network:type=SocketServer,name=NetworkProcessorAvgIdlePercent/FiveMinuteRate;" + \
          "kafka.network.socketserver.networkprocessoravgidlepercent.fifteenminuterate=kafka.network:type=SocketServer,name=NetworkProcessorAvgIdlePercent/FifteenMinuteRate;" + \
          "kafka.network.requestchannel.responsequeuesize.processor.2.value=kafka.network:type=RequestChannel,name=ResponseQueueSize,processor=2/Value;" + \
          "kafka.server.brokertopicmetrics.messagesinpersec.count=kafka.server:type=BrokerTopicMetrics,name=MessagesInPerSec/Count;" + \
          "kafka.server.brokertopicmetrics.messagesinpersec.eventtype=kafka.server:type=BrokerTopicMetrics,name=MessagesInPerSec/EventType;" + \
          "kafka.server.brokertopicmetrics.messagesinpersec.rateunit=kafka.server:type=BrokerTopicMetrics,name=MessagesInPerSec/RateUnit;" + \
          "kafka.server.brokertopicmetrics.messagesinpersec.meanrate=kafka.server:type=BrokerTopicMetrics,name=MessagesInPerSec/MeanRate;" + \
          "kafka.server.brokertopicmetrics.messagesinpersec.oneminuterate=kafka.server:type=BrokerTopicMetrics,name=MessagesInPerSec/OneMinuteRate;" + \
          "kafka.server.brokertopicmetrics.messagesinpersec.fiveminuterate=kafka.server:type=BrokerTopicMetrics,name=MessagesInPerSec/FiveMinuteRate;" + \
          "kafka.server.brokertopicmetrics.messagesinpersec.fifteenminuterate=kafka.server:type=BrokerTopicMetrics,name=MessagesInPerSec/FifteenMinuteRate;" + \
          "kafka.server.offsetmanager.numgroups.value=kafka.server:type=OffsetManager,name=NumGroups/Value;" + \
          "kafka.controller.kafkacontroller.activecontrollercount.value=kafka.controller:type=KafkaController,name=ActiveControllerCount/Value;" + \
          "kafka.kafka.log4jcontroller.loggers=kafka:type=kafka.Log4jController/Loggers;" + \
          "kafka.server.replicamanager.partitioncount.value=kafka.server:type=ReplicaManager,name=PartitionCount/Value;" + \
          "kafka.controller.controllerstats.leaderelectionrateandtimems.latencyunit=kafka.controller:type=ControllerStats,name=LeaderElectionRateAndTimeMs/LatencyUnit;" + \
          "kafka.controller.controllerstats.leaderelectionrateandtimems.eventtype=kafka.controller:type=ControllerStats,name=LeaderElectionRateAndTimeMs/EventType;" + \
          "kafka.controller.controllerstats.leaderelectionrateandtimems.rateunit=kafka.controller:type=ControllerStats,name=LeaderElectionRateAndTimeMs/RateUnit;" + \
          "kafka.controller.controllerstats.leaderelectionrateandtimems.meanrate=kafka.controller:type=ControllerStats,name=LeaderElectionRateAndTimeMs/MeanRate;" + \
          "kafka.controller.controllerstats.leaderelectionrateandtimems.oneminuterate=kafka.controller:type=ControllerStats,name=LeaderElectionRateAndTimeMs/OneMinuteRate;" + \
          "kafka.controller.controllerstats.leaderelectionrateandtimems.fiveminuterate=kafka.controller:type=ControllerStats,name=LeaderElectionRateAndTimeMs/FiveMinuteRate;" + \
          "kafka.controller.controllerstats.leaderelectionrateandtimems.fifteenminuterate=kafka.controller:type=ControllerStats,name=LeaderElectionRateAndTimeMs/FifteenMinuteRate;" + \
          "kafka.controller.controllerstats.leaderelectionrateandtimems.count=kafka.controller:type=ControllerStats,name=LeaderElectionRateAndTimeMs/Count;" + \
          "kafka.controller.controllerstats.leaderelectionrateandtimems.max=kafka.controller:type=ControllerStats,name=LeaderElectionRateAndTimeMs/Max;" + \
          "kafka.controller.controllerstats.leaderelectionrateandtimems.50thpercentile=kafka.controller:type=ControllerStats,name=LeaderElectionRateAndTimeMs/50thPercentile;" + \
          "kafka.controller.controllerstats.leaderelectionrateandtimems.75thpercentile=kafka.controller:type=ControllerStats,name=LeaderElectionRateAndTimeMs/75thPercentile;" + \
          "kafka.controller.controllerstats.leaderelectionrateandtimems.min=kafka.controller:type=ControllerStats,name=LeaderElectionRateAndTimeMs/Min;" + \
          "kafka.controller.controllerstats.leaderelectionrateandtimems.mean=kafka.controller:type=ControllerStats,name=LeaderElectionRateAndTimeMs/Mean;" + \
          "kafka.controller.controllerstats.leaderelectionrateandtimems.stddev=kafka.controller:type=ControllerStats,name=LeaderElectionRateAndTimeMs/StdDev;" + \
          "kafka.controller.controllerstats.leaderelectionrateandtimems.95thpercentile=kafka.controller:type=ControllerStats,name=LeaderElectionRateAndTimeMs/95thPercentile;" + \
          "kafka.controller.controllerstats.leaderelectionrateandtimems.98thpercentile=kafka.controller:type=ControllerStats,name=LeaderElectionRateAndTimeMs/98thPercentile;" + \
          "kafka.controller.controllerstats.leaderelectionrateandtimems.99thpercentile=kafka.controller:type=ControllerStats,name=LeaderElectionRateAndTimeMs/99thPercentile;" + \
          "kafka.controller.controllerstats.leaderelectionrateandtimems.999thpercentile=kafka.controller:type=ControllerStats,name=LeaderElectionRateAndTimeMs/999thPercentile;" + \
          "kafka.server.brokertopicmetrics.failedproducerequestspersec.count=kafka.server:type=BrokerTopicMetrics,name=FailedProduceRequestsPerSec/Count;" + \
          "kafka.server.brokertopicmetrics.failedproducerequestspersec.eventtype=kafka.server:type=BrokerTopicMetrics,name=FailedProduceRequestsPerSec/EventType;" + \
          "kafka.server.brokertopicmetrics.failedproducerequestspersec.rateunit=kafka.server:type=BrokerTopicMetrics,name=FailedProduceRequestsPerSec/RateUnit;" + \
          "kafka.server.brokertopicmetrics.failedproducerequestspersec.meanrate=kafka.server:type=BrokerTopicMetrics,name=FailedProduceRequestsPerSec/MeanRate;" + \
          "kafka.server.brokertopicmetrics.failedproducerequestspersec.oneminuterate=kafka.server:type=BrokerTopicMetrics,name=FailedProduceRequestsPerSec/OneMinuteRate;" + \
          "kafka.server.brokertopicmetrics.failedproducerequestspersec.fiveminuterate=kafka.server:type=BrokerTopicMetrics,name=FailedProduceRequestsPerSec/FiveMinuteRate;" + \
          "kafka.server.brokertopicmetrics.failedproducerequestspersec.fifteenminuterate=kafka.server:type=BrokerTopicMetrics,name=FailedProduceRequestsPerSec/FifteenMinuteRate;" + \
          "kafka.server.producerrequestpurgatory.numdelayedrequests.value=kafka.server:type=ProducerRequestPurgatory,name=NumDelayedRequests/Value;" + \
          "kafka.server.replicamanager.underreplicatedpartitions.value=kafka.server:type=ReplicaManager,name=UnderReplicatedPartitions/Value;" + \
          "kafka.controller.controllerstats.uncleanleaderelectionspersec.count=kafka.controller:type=ControllerStats,name=UncleanLeaderElectionsPerSec/Count;" + \
          "kafka.controller.controllerstats.uncleanleaderelectionspersec.eventtype=kafka.controller:type=ControllerStats,name=UncleanLeaderElectionsPerSec/EventType;" + \
          "kafka.controller.controllerstats.uncleanleaderelectionspersec.rateunit=kafka.controller:type=ControllerStats,name=UncleanLeaderElectionsPerSec/RateUnit;" + \
          "kafka.controller.controllerstats.uncleanleaderelectionspersec.meanrate=kafka.controller:type=ControllerStats,name=UncleanLeaderElectionsPerSec/MeanRate;" + \
          "kafka.controller.controllerstats.uncleanleaderelectionspersec.oneminuterate=kafka.controller:type=ControllerStats,name=UncleanLeaderElectionsPerSec/OneMinuteRate;" + \
          "kafka.controller.controllerstats.uncleanleaderelectionspersec.fiveminuterate=kafka.controller:type=ControllerStats,name=UncleanLeaderElectionsPerSec/FiveMinuteRate;" + \
          "kafka.controller.controllerstats.uncleanleaderelectionspersec.fifteenminuterate=kafka.controller:type=ControllerStats,name=UncleanLeaderElectionsPerSec/FifteenMinuteRate;" + \
          "kafka.server.brokertopicmetrics.bytesinpersec.count=kafka.server:type=BrokerTopicMetrics,name=BytesInPerSec/Count;" + \
          "kafka.server.brokertopicmetrics.bytesinpersec.eventtype=kafka.server:type=BrokerTopicMetrics,name=BytesInPerSec/EventType;" + \
          "kafka.server.brokertopicmetrics.bytesinpersec.rateunit=kafka.server:type=BrokerTopicMetrics,name=BytesInPerSec/RateUnit;" + \
          "kafka.server.brokertopicmetrics.bytesinpersec.meanrate=kafka.server:type=BrokerTopicMetrics,name=BytesInPerSec/MeanRate;" + \
          "kafka.server.brokertopicmetrics.bytesinpersec.oneminuterate=kafka.server:type=BrokerTopicMetrics,name=BytesInPerSec/OneMinuteRate;" + \
          "kafka.server.brokertopicmetrics.bytesinpersec.fiveminuterate=kafka.server:type=BrokerTopicMetrics,name=BytesInPerSec/FiveMinuteRate;" + \
          "kafka.server.brokertopicmetrics.bytesinpersec.fifteenminuterate=kafka.server:type=BrokerTopicMetrics,name=BytesInPerSec/FifteenMinuteRate;" + \
          "kafka.server.delayedfetchrequestmetrics.followerexpirespersecond.count=kafka.server:type=DelayedFetchRequestMetrics,name=FollowerExpiresPerSecond/Count;" + \
          "kafka.server.delayedfetchrequestmetrics.followerexpirespersecond.eventtype=kafka.server:type=DelayedFetchRequestMetrics,name=FollowerExpiresPerSecond/EventType;" + \
          "kafka.server.delayedfetchrequestmetrics.followerexpirespersecond.rateunit=kafka.server:type=DelayedFetchRequestMetrics,name=FollowerExpiresPerSecond/RateUnit;" + \
          "kafka.server.delayedfetchrequestmetrics.followerexpirespersecond.meanrate=kafka.server:type=DelayedFetchRequestMetrics,name=FollowerExpiresPerSecond/MeanRate;" + \
          "kafka.server.delayedfetchrequestmetrics.followerexpirespersecond.oneminuterate=kafka.server:type=DelayedFetchRequestMetrics,name=FollowerExpiresPerSecond/OneMinuteRate;" + \
          "kafka.server.delayedfetchrequestmetrics.followerexpirespersecond.fiveminuterate=kafka.server:type=DelayedFetchRequestMetrics,name=FollowerExpiresPerSecond/FiveMinuteRate;" + \
          "kafka.server.delayedfetchrequestmetrics.followerexpirespersecond.fifteenminuterate=kafka.server:type=DelayedFetchRequestMetrics,name=FollowerExpiresPerSecond/FifteenMinuteRate;" + \
          "kafka.server.replicamanager.leadercount.value=kafka.server:type=ReplicaManager,name=LeaderCount/Value;" + \
          "kafka.server.brokertopicmetrics.failedfetchrequestspersec.count=kafka.server:type=BrokerTopicMetrics,name=FailedFetchRequestsPerSec/Count;" + \
          "kafka.server.brokertopicmetrics.failedfetchrequestspersec.eventtype=kafka.server:type=BrokerTopicMetrics,name=FailedFetchRequestsPerSec/EventType;" + \
          "kafka.server.brokertopicmetrics.failedfetchrequestspersec.rateunit=kafka.server:type=BrokerTopicMetrics,name=FailedFetchRequestsPerSec/RateUnit;" + \
          "kafka.server.brokertopicmetrics.failedfetchrequestspersec.meanrate=kafka.server:type=BrokerTopicMetrics,name=FailedFetchRequestsPerSec/MeanRate;" + \
          "kafka.server.brokertopicmetrics.failedfetchrequestspersec.oneminuterate=kafka.server:type=BrokerTopicMetrics,name=FailedFetchRequestsPerSec/OneMinuteRate;" + \
          "kafka.server.brokertopicmetrics.failedfetchrequestspersec.fiveminuterate=kafka.server:type=BrokerTopicMetrics,name=FailedFetchRequestsPerSec/FiveMinuteRate;" + \
          "kafka.server.brokertopicmetrics.failedfetchrequestspersec.fifteenminuterate=kafka.server:type=BrokerTopicMetrics,name=FailedFetchRequestsPerSec/FifteenMinuteRate;" + \
          "kafka.server.replicamanager.isrshrinkspersec.count=kafka.server:type=ReplicaManager,name=IsrShrinksPerSec/Count;" + \
          "kafka.server.replicamanager.isrshrinkspersec.eventtype=kafka.server:type=ReplicaManager,name=IsrShrinksPerSec/EventType;" + \
          "kafka.server.replicamanager.isrshrinkspersec.rateunit=kafka.server:type=ReplicaManager,name=IsrShrinksPerSec/RateUnit;" + \
          "kafka.server.replicamanager.isrshrinkspersec.meanrate=kafka.server:type=ReplicaManager,name=IsrShrinksPerSec/MeanRate;" + \
          "kafka.server.replicamanager.isrshrinkspersec.oneminuterate=kafka.server:type=ReplicaManager,name=IsrShrinksPerSec/OneMinuteRate;" + \
          "kafka.server.replicamanager.isrshrinkspersec.fiveminuterate=kafka.server:type=ReplicaManager,name=IsrShrinksPerSec/FiveMinuteRate;" + \
          "kafka.server.replicamanager.isrshrinkspersec.fifteenminuterate=kafka.server:type=ReplicaManager,name=IsrShrinksPerSec/FifteenMinuteRate;" + \
          "kafka.server.delayedfetchrequestmetrics.consumerexpirespersecond.count=kafka.server:type=DelayedFetchRequestMetrics,name=ConsumerExpiresPerSecond/Count;" + \
          "kafka.server.delayedfetchrequestmetrics.consumerexpirespersecond.eventtype=kafka.server:type=DelayedFetchRequestMetrics,name=ConsumerExpiresPerSecond/EventType;" + \
          "kafka.server.delayedfetchrequestmetrics.consumerexpirespersecond.rateunit=kafka.server:type=DelayedFetchRequestMetrics,name=ConsumerExpiresPerSecond/RateUnit;" + \
          "kafka.server.delayedfetchrequestmetrics.consumerexpirespersecond.meanrate=kafka.server:type=DelayedFetchRequestMetrics,name=ConsumerExpiresPerSecond/MeanRate;" + \
          "kafka.server.delayedfetchrequestmetrics.consumerexpirespersecond.oneminuterate=kafka.server:type=DelayedFetchRequestMetrics,name=ConsumerExpiresPerSecond/OneMinuteRate;" + \
          "kafka.server.delayedfetchrequestmetrics.consumerexpirespersecond.fiveminuterate=kafka.server:type=DelayedFetchRequestMetrics,name=ConsumerExpiresPerSecond/FiveMinuteRate;" + \
          "kafka.server.delayedfetchrequestmetrics.consumerexpirespersecond.fifteenminuterate=kafka.server:type=DelayedFetchRequestMetrics,name=ConsumerExpiresPerSecond/FifteenMinuteRate;" + \
          "kafka.network.socketserver.idlepercent.networkprocessor.2.count=kafka.network:type=SocketServer,name=IdlePercent,networkProcessor=2/Count;" + \
          "kafka.network.socketserver.idlepercent.networkprocessor.2.eventtype=kafka.network:type=SocketServer,name=IdlePercent,networkProcessor=2/EventType;" + \
          "kafka.network.socketserver.idlepercent.networkprocessor.2.rateunit=kafka.network:type=SocketServer,name=IdlePercent,networkProcessor=2/RateUnit;" + \
          "kafka.network.socketserver.idlepercent.networkprocessor.2.meanrate=kafka.network:type=SocketServer,name=IdlePercent,networkProcessor=2/MeanRate;" + \
          "kafka.network.socketserver.idlepercent.networkprocessor.2.oneminuterate=kafka.network:type=SocketServer,name=IdlePercent,networkProcessor=2/OneMinuteRate;" + \
          "kafka.network.socketserver.idlepercent.networkprocessor.2.fiveminuterate=kafka.network:type=SocketServer,name=IdlePercent,networkProcessor=2/FiveMinuteRate;" + \
          "kafka.network.socketserver.idlepercent.networkprocessor.2.fifteenminuterate=kafka.network:type=SocketServer,name=IdlePercent,networkProcessor=2/FifteenMinuteRate;" + \
          "kafka.network.socketserver.responsesbeingsent.value=kafka.network:type=SocketServer,name=ResponsesBeingSent/Value;" + \
          "kafka.network.requestchannel.responsequeuesize.processor.1.value=kafka.network:type=RequestChannel,name=ResponseQueueSize,processor=1/Value;" + \
          "kafka.server.replicamanager.isrexpandspersec.count=kafka.server:type=ReplicaManager,name=IsrExpandsPerSec/Count;" + \
          "kafka.server.replicamanager.isrexpandspersec.eventtype=kafka.server:type=ReplicaManager,name=IsrExpandsPerSec/EventType;" + \
          "kafka.server.replicamanager.isrexpandspersec.rateunit=kafka.server:type=ReplicaManager,name=IsrExpandsPerSec/RateUnit;" + \
          "kafka.server.replicamanager.isrexpandspersec.meanrate=kafka.server:type=ReplicaManager,name=IsrExpandsPerSec/MeanRate;" + \
          "kafka.server.replicamanager.isrexpandspersec.oneminuterate=kafka.server:type=ReplicaManager,name=IsrExpandsPerSec/OneMinuteRate;" + \
          "kafka.server.replicamanager.isrexpandspersec.fiveminuterate=kafka.server:type=ReplicaManager,name=IsrExpandsPerSec/FiveMinuteRate;" + \
          "kafka.server.replicamanager.isrexpandspersec.fifteenminuterate=kafka.server:type=ReplicaManager,name=IsrExpandsPerSec/FifteenMinuteRate;"


def is_digit(d):
    try:
        float(d)
    except ValueError:
        return False
    return True


def get_metrics():
    command = [JAVA_BIN, '-jar', '../embedded/lib/jmxquery.jar', '-url', JMX_URL, '-metrics', METRICS, '-json', '-incjvm']
    if JMX_USERNAME:
        command.extend(['-username', JMX_USERNAME, '-password', JMX_PASSWORD])
    jsonOutput = ""

    try:
        jsonOutput = subprocess.check_output(command)
    except:
        print "Error connecting to JMX URL '" + JMX_URL + "'. Please check URL and that JMX is enabled on Java process"
        exit(2)

    metrics = json.loads(jsonOutput)

    # Print Nagios output
    output = "OK | "
    for metric in metrics:
        if 'value' in metric.keys():
            value = metric['value']
            if is_digit(value):
                output += metric['metricName'] + "=" + str(round(float(value), 2)) + ";;;; "
    print output


get_metrics()