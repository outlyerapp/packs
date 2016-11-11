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

METRICS = "server.delayedproducerrequestmetrics.expirespersecond.count=kafka.server:type=DelayedProducerRequestMetrics,name=ExpiresPerSecond/Count;" + \
          "server.delayedproducerrequestmetrics.expirespersecond.eventtype=kafka.server:type=DelayedProducerRequestMetrics,name=ExpiresPerSecond/EventType;" + \
          "server.delayedproducerrequestmetrics.expirespersecond.rateunit=kafka.server:type=DelayedProducerRequestMetrics,name=ExpiresPerSecond/RateUnit;" + \
          "server.delayedproducerrequestmetrics.expirespersecond.meanrate=kafka.server:type=DelayedProducerRequestMetrics,name=ExpiresPerSecond/MeanRate;" + \
          "server.delayedproducerrequestmetrics.expirespersecond.oneminuterate=kafka.server:type=DelayedProducerRequestMetrics,name=ExpiresPerSecond/OneMinuteRate;" + \
          "server.delayedproducerrequestmetrics.expirespersecond.fiveminuterate=kafka.server:type=DelayedProducerRequestMetrics,name=ExpiresPerSecond/FiveMinuteRate;" + \
          "server.delayedproducerrequestmetrics.expirespersecond.fifteenminuterate=kafka.server:type=DelayedProducerRequestMetrics,name=ExpiresPerSecond/FifteenMinuteRate;" + \
          "server.producerrequestpurgatory.purgatorysize.value=kafka.server:type=ProducerRequestPurgatory,name=PurgatorySize/Value;" + \
          "server.brokertopicmetrics.bytesrejectedpersec.count=kafka.server:type=BrokerTopicMetrics,name=BytesRejectedPerSec/Count;" + \
          "server.brokertopicmetrics.bytesrejectedpersec.eventtype=kafka.server:type=BrokerTopicMetrics,name=BytesRejectedPerSec/EventType;" + \
          "server.brokertopicmetrics.bytesrejectedpersec.rateunit=kafka.server:type=BrokerTopicMetrics,name=BytesRejectedPerSec/RateUnit;" + \
          "server.brokertopicmetrics.bytesrejectedpersec.meanrate=kafka.server:type=BrokerTopicMetrics,name=BytesRejectedPerSec/MeanRate;" + \
          "server.brokertopicmetrics.bytesrejectedpersec.oneminuterate=kafka.server:type=BrokerTopicMetrics,name=BytesRejectedPerSec/OneMinuteRate;" + \
          "server.brokertopicmetrics.bytesrejectedpersec.fiveminuterate=kafka.server:type=BrokerTopicMetrics,name=BytesRejectedPerSec/FiveMinuteRate;" + \
          "server.brokertopicmetrics.bytesrejectedpersec.fifteenminuterate=kafka.server:type=BrokerTopicMetrics,name=BytesRejectedPerSec/FifteenMinuteRate;" + \
          "network.requestchannel.responsequeuesize.value=kafka.network:type=RequestChannel,name=ResponseQueueSize/Value;" + \
          "network.socketserver.idlepercent.networkprocessor.1.count=kafka.network:type=SocketServer,name=IdlePercent,networkProcessor=1/Count;" + \
          "network.socketserver.idlepercent.networkprocessor.1.eventtype=kafka.network:type=SocketServer,name=IdlePercent,networkProcessor=1/EventType;" + \
          "network.socketserver.idlepercent.networkprocessor.1.rateunit=kafka.network:type=SocketServer,name=IdlePercent,networkProcessor=1/RateUnit;" + \
          "network.socketserver.idlepercent.networkprocessor.1.meanrate=kafka.network:type=SocketServer,name=IdlePercent,networkProcessor=1/MeanRate;" + \
          "network.socketserver.idlepercent.networkprocessor.1.oneminuterate=kafka.network:type=SocketServer,name=IdlePercent,networkProcessor=1/OneMinuteRate;" + \
          "network.socketserver.idlepercent.networkprocessor.1.fiveminuterate=kafka.network:type=SocketServer,name=IdlePercent,networkProcessor=1/FiveMinuteRate;" + \
          "network.socketserver.idlepercent.networkprocessor.1.fifteenminuterate=kafka.network:type=SocketServer,name=IdlePercent,networkProcessor=1/FifteenMinuteRate;" + \
          "server.offsetmanager.numoffsets.value=kafka.server:type=OffsetManager,name=NumOffsets/Value;" + \
          "network.requestchannel.responsequeuesize.processor.0.value=kafka.network:type=RequestChannel,name=ResponseQueueSize,processor=0/Value;" + \
          "server.kafkaserver.brokerstate.value=kafka.server:type=KafkaServer,name=BrokerState/Value;" + \
          "controller.kafkacontroller.offlinepartitionscount.value=kafka.controller:type=KafkaController,name=OfflinePartitionsCount/Value;" + \
          "server.kafkarequesthandlerpool.requesthandleravgidlepercent.count=kafka.server:type=KafkaRequestHandlerPool,name=RequestHandlerAvgIdlePercent/Count;" + \
          "server.kafkarequesthandlerpool.requesthandleravgidlepercent.eventtype=kafka.server:type=KafkaRequestHandlerPool,name=RequestHandlerAvgIdlePercent/EventType;" + \
          "server.kafkarequesthandlerpool.requesthandleravgidlepercent.rateunit=kafka.server:type=KafkaRequestHandlerPool,name=RequestHandlerAvgIdlePercent/RateUnit;" + \
          "server.kafkarequesthandlerpool.requesthandleravgidlepercent.meanrate=kafka.server:type=KafkaRequestHandlerPool,name=RequestHandlerAvgIdlePercent/MeanRate;" + \
          "server.kafkarequesthandlerpool.requesthandleravgidlepercent.oneminuterate=kafka.server:type=KafkaRequestHandlerPool,name=RequestHandlerAvgIdlePercent/OneMinuteRate;" + \
          "server.kafkarequesthandlerpool.requesthandleravgidlepercent.fiveminuterate=kafka.server:type=KafkaRequestHandlerPool,name=RequestHandlerAvgIdlePercent/FiveMinuteRate;" + \
          "server.kafkarequesthandlerpool.requesthandleravgidlepercent.fifteenminuterate=kafka.server:type=KafkaRequestHandlerPool,name=RequestHandlerAvgIdlePercent/FifteenMinuteRate;" + \
          "network.socketserver.idlepercent.networkprocessor.0.count=kafka.network:type=SocketServer,name=IdlePercent,networkProcessor=0/Count;" + \
          "network.socketserver.idlepercent.networkprocessor.0.eventtype=kafka.network:type=SocketServer,name=IdlePercent,networkProcessor=0/EventType;" + \
          "network.socketserver.idlepercent.networkprocessor.0.rateunit=kafka.network:type=SocketServer,name=IdlePercent,networkProcessor=0/RateUnit;" + \
          "network.socketserver.idlepercent.networkprocessor.0.meanrate=kafka.network:type=SocketServer,name=IdlePercent,networkProcessor=0/MeanRate;" + \
          "network.socketserver.idlepercent.networkprocessor.0.oneminuterate=kafka.network:type=SocketServer,name=IdlePercent,networkProcessor=0/OneMinuteRate;" + \
          "network.socketserver.idlepercent.networkprocessor.0.fiveminuterate=kafka.network:type=SocketServer,name=IdlePercent,networkProcessor=0/FiveMinuteRate;" + \
          "network.socketserver.idlepercent.networkprocessor.0.fifteenminuterate=kafka.network:type=SocketServer,name=IdlePercent,networkProcessor=0/FifteenMinuteRate;" + \
          "common.appinfo.version.value=kafka.common:type=AppInfo,name=Version/Value;" + \
          "network.requestchannel.requestqueuesize.value=kafka.network:type=RequestChannel,name=RequestQueueSize/Value;" + \
          "server.replicafetchermanager.maxlag.clientid.replica.value=kafka.server:type=ReplicaFetcherManager,name=MaxLag,clientId=Replica/Value;" + \
          "server.fetchrequestpurgatory.numdelayedrequests.value=kafka.server:type=FetchRequestPurgatory,name=NumDelayedRequests/Value;" + \
          "server.replicafetchermanager.minfetchrate.clientid.replica.value=kafka.server:type=ReplicaFetcherManager,name=MinFetchRate,clientId=Replica/Value;" + \
          "server.fetchrequestpurgatory.purgatorysize.value=kafka.server:type=FetchRequestPurgatory,name=PurgatorySize/Value;" + \
          "controller.kafkacontroller.preferredreplicaimbalancecount.value=kafka.controller:type=KafkaController,name=PreferredReplicaImbalanceCount/Value;" + \
          "server.brokertopicmetrics.bytesoutpersec.count=kafka.server:type=BrokerTopicMetrics,name=BytesOutPerSec/Count;" + \
          "server.brokertopicmetrics.bytesoutpersec.eventtype=kafka.server:type=BrokerTopicMetrics,name=BytesOutPerSec/EventType;" + \
          "server.brokertopicmetrics.bytesoutpersec.rateunit=kafka.server:type=BrokerTopicMetrics,name=BytesOutPerSec/RateUnit;" + \
          "server.brokertopicmetrics.bytesoutpersec.meanrate=kafka.server:type=BrokerTopicMetrics,name=BytesOutPerSec/MeanRate;" + \
          "server.brokertopicmetrics.bytesoutpersec.oneminuterate=kafka.server:type=BrokerTopicMetrics,name=BytesOutPerSec/OneMinuteRate;" + \
          "server.brokertopicmetrics.bytesoutpersec.fiveminuterate=kafka.server:type=BrokerTopicMetrics,name=BytesOutPerSec/FiveMinuteRate;" + \
          "server.brokertopicmetrics.bytesoutpersec.fifteenminuterate=kafka.server:type=BrokerTopicMetrics,name=BytesOutPerSec/FifteenMinuteRate;" + \
          "network.socketserver.networkprocessoravgidlepercent.count=kafka.network:type=SocketServer,name=NetworkProcessorAvgIdlePercent/Count;" + \
          "network.socketserver.networkprocessoravgidlepercent.eventtype=kafka.network:type=SocketServer,name=NetworkProcessorAvgIdlePercent/EventType;" + \
          "network.socketserver.networkprocessoravgidlepercent.rateunit=kafka.network:type=SocketServer,name=NetworkProcessorAvgIdlePercent/RateUnit;" + \
          "network.socketserver.networkprocessoravgidlepercent.meanrate=kafka.network:type=SocketServer,name=NetworkProcessorAvgIdlePercent/MeanRate;" + \
          "network.socketserver.networkprocessoravgidlepercent.oneminuterate=kafka.network:type=SocketServer,name=NetworkProcessorAvgIdlePercent/OneMinuteRate;" + \
          "network.socketserver.networkprocessoravgidlepercent.fiveminuterate=kafka.network:type=SocketServer,name=NetworkProcessorAvgIdlePercent/FiveMinuteRate;" + \
          "network.socketserver.networkprocessoravgidlepercent.fifteenminuterate=kafka.network:type=SocketServer,name=NetworkProcessorAvgIdlePercent/FifteenMinuteRate;" + \
          "network.requestchannel.responsequeuesize.processor.2.value=kafka.network:type=RequestChannel,name=ResponseQueueSize,processor=2/Value;" + \
          "server.brokertopicmetrics.messagesinpersec.count=kafka.server:type=BrokerTopicMetrics,name=MessagesInPerSec/Count;" + \
          "server.brokertopicmetrics.messagesinpersec.eventtype=kafka.server:type=BrokerTopicMetrics,name=MessagesInPerSec/EventType;" + \
          "server.brokertopicmetrics.messagesinpersec.rateunit=kafka.server:type=BrokerTopicMetrics,name=MessagesInPerSec/RateUnit;" + \
          "server.brokertopicmetrics.messagesinpersec.meanrate=kafka.server:type=BrokerTopicMetrics,name=MessagesInPerSec/MeanRate;" + \
          "server.brokertopicmetrics.messagesinpersec.oneminuterate=kafka.server:type=BrokerTopicMetrics,name=MessagesInPerSec/OneMinuteRate;" + \
          "server.brokertopicmetrics.messagesinpersec.fiveminuterate=kafka.server:type=BrokerTopicMetrics,name=MessagesInPerSec/FiveMinuteRate;" + \
          "server.brokertopicmetrics.messagesinpersec.fifteenminuterate=kafka.server:type=BrokerTopicMetrics,name=MessagesInPerSec/FifteenMinuteRate;" + \
          "server.offsetmanager.numgroups.value=kafka.server:type=OffsetManager,name=NumGroups/Value;" + \
          "controller.kafkacontroller.activecontrollercount.value=kafka.controller:type=KafkaController,name=ActiveControllerCount/Value;" + \
          "log4jcontroller.loggers=kafka:type=kafka.Log4jController/Loggers;" + \
          "server.replicamanager.partitioncount.value=kafka.server:type=ReplicaManager,name=PartitionCount/Value;" + \
          "controller.controllerstats.leaderelectionrateandtimems.latencyunit=kafka.controller:type=ControllerStats,name=LeaderElectionRateAndTimeMs/LatencyUnit;" + \
          "controller.controllerstats.leaderelectionrateandtimems.eventtype=kafka.controller:type=ControllerStats,name=LeaderElectionRateAndTimeMs/EventType;" + \
          "controller.controllerstats.leaderelectionrateandtimems.rateunit=kafka.controller:type=ControllerStats,name=LeaderElectionRateAndTimeMs/RateUnit;" + \
          "controller.controllerstats.leaderelectionrateandtimems.meanrate=kafka.controller:type=ControllerStats,name=LeaderElectionRateAndTimeMs/MeanRate;" + \
          "controller.controllerstats.leaderelectionrateandtimems.oneminuterate=kafka.controller:type=ControllerStats,name=LeaderElectionRateAndTimeMs/OneMinuteRate;" + \
          "controller.controllerstats.leaderelectionrateandtimems.fiveminuterate=kafka.controller:type=ControllerStats,name=LeaderElectionRateAndTimeMs/FiveMinuteRate;" + \
          "controller.controllerstats.leaderelectionrateandtimems.fifteenminuterate=kafka.controller:type=ControllerStats,name=LeaderElectionRateAndTimeMs/FifteenMinuteRate;" + \
          "controller.controllerstats.leaderelectionrateandtimems.count=kafka.controller:type=ControllerStats,name=LeaderElectionRateAndTimeMs/Count;" + \
          "controller.controllerstats.leaderelectionrateandtimems.max=kafka.controller:type=ControllerStats,name=LeaderElectionRateAndTimeMs/Max;" + \
          "controller.controllerstats.leaderelectionrateandtimems.50thpercentile=kafka.controller:type=ControllerStats,name=LeaderElectionRateAndTimeMs/50thPercentile;" + \
          "controller.controllerstats.leaderelectionrateandtimems.75thpercentile=kafka.controller:type=ControllerStats,name=LeaderElectionRateAndTimeMs/75thPercentile;" + \
          "controller.controllerstats.leaderelectionrateandtimems.min=kafka.controller:type=ControllerStats,name=LeaderElectionRateAndTimeMs/Min;" + \
          "controller.controllerstats.leaderelectionrateandtimems.mean=kafka.controller:type=ControllerStats,name=LeaderElectionRateAndTimeMs/Mean;" + \
          "controller.controllerstats.leaderelectionrateandtimems.stddev=kafka.controller:type=ControllerStats,name=LeaderElectionRateAndTimeMs/StdDev;" + \
          "controller.controllerstats.leaderelectionrateandtimems.95thpercentile=kafka.controller:type=ControllerStats,name=LeaderElectionRateAndTimeMs/95thPercentile;" + \
          "controller.controllerstats.leaderelectionrateandtimems.98thpercentile=kafka.controller:type=ControllerStats,name=LeaderElectionRateAndTimeMs/98thPercentile;" + \
          "controller.controllerstats.leaderelectionrateandtimems.99thpercentile=kafka.controller:type=ControllerStats,name=LeaderElectionRateAndTimeMs/99thPercentile;" + \
          "controller.controllerstats.leaderelectionrateandtimems.999thpercentile=kafka.controller:type=ControllerStats,name=LeaderElectionRateAndTimeMs/999thPercentile;" + \
          "server.brokertopicmetrics.failedproducerequestspersec.count=kafka.server:type=BrokerTopicMetrics,name=FailedProduceRequestsPerSec/Count;" + \
          "server.brokertopicmetrics.failedproducerequestspersec.eventtype=kafka.server:type=BrokerTopicMetrics,name=FailedProduceRequestsPerSec/EventType;" + \
          "server.brokertopicmetrics.failedproducerequestspersec.rateunit=kafka.server:type=BrokerTopicMetrics,name=FailedProduceRequestsPerSec/RateUnit;" + \
          "server.brokertopicmetrics.failedproducerequestspersec.meanrate=kafka.server:type=BrokerTopicMetrics,name=FailedProduceRequestsPerSec/MeanRate;" + \
          "server.brokertopicmetrics.failedproducerequestspersec.oneminuterate=kafka.server:type=BrokerTopicMetrics,name=FailedProduceRequestsPerSec/OneMinuteRate;" + \
          "server.brokertopicmetrics.failedproducerequestspersec.fiveminuterate=kafka.server:type=BrokerTopicMetrics,name=FailedProduceRequestsPerSec/FiveMinuteRate;" + \
          "server.brokertopicmetrics.failedproducerequestspersec.fifteenminuterate=kafka.server:type=BrokerTopicMetrics,name=FailedProduceRequestsPerSec/FifteenMinuteRate;" + \
          "server.producerrequestpurgatory.numdelayedrequests.value=kafka.server:type=ProducerRequestPurgatory,name=NumDelayedRequests/Value;" + \
          "server.replicamanager.underreplicatedpartitions.value=kafka.server:type=ReplicaManager,name=UnderReplicatedPartitions/Value;" + \
          "controller.controllerstats.uncleanleaderelectionspersec.count=kafka.controller:type=ControllerStats,name=UncleanLeaderElectionsPerSec/Count;" + \
          "controller.controllerstats.uncleanleaderelectionspersec.eventtype=kafka.controller:type=ControllerStats,name=UncleanLeaderElectionsPerSec/EventType;" + \
          "controller.controllerstats.uncleanleaderelectionspersec.rateunit=kafka.controller:type=ControllerStats,name=UncleanLeaderElectionsPerSec/RateUnit;" + \
          "controller.controllerstats.uncleanleaderelectionspersec.meanrate=kafka.controller:type=ControllerStats,name=UncleanLeaderElectionsPerSec/MeanRate;" + \
          "controller.controllerstats.uncleanleaderelectionspersec.oneminuterate=kafka.controller:type=ControllerStats,name=UncleanLeaderElectionsPerSec/OneMinuteRate;" + \
          "controller.controllerstats.uncleanleaderelectionspersec.fiveminuterate=kafka.controller:type=ControllerStats,name=UncleanLeaderElectionsPerSec/FiveMinuteRate;" + \
          "controller.controllerstats.uncleanleaderelectionspersec.fifteenminuterate=kafka.controller:type=ControllerStats,name=UncleanLeaderElectionsPerSec/FifteenMinuteRate;" + \
          "server.brokertopicmetrics.bytesinpersec.count=kafka.server:type=BrokerTopicMetrics,name=BytesInPerSec/Count;" + \
          "server.brokertopicmetrics.bytesinpersec.eventtype=kafka.server:type=BrokerTopicMetrics,name=BytesInPerSec/EventType;" + \
          "server.brokertopicmetrics.bytesinpersec.rateunit=kafka.server:type=BrokerTopicMetrics,name=BytesInPerSec/RateUnit;" + \
          "server.brokertopicmetrics.bytesinpersec.meanrate=kafka.server:type=BrokerTopicMetrics,name=BytesInPerSec/MeanRate;" + \
          "server.brokertopicmetrics.bytesinpersec.oneminuterate=kafka.server:type=BrokerTopicMetrics,name=BytesInPerSec/OneMinuteRate;" + \
          "server.brokertopicmetrics.bytesinpersec.fiveminuterate=kafka.server:type=BrokerTopicMetrics,name=BytesInPerSec/FiveMinuteRate;" + \
          "server.brokertopicmetrics.bytesinpersec.fifteenminuterate=kafka.server:type=BrokerTopicMetrics,name=BytesInPerSec/FifteenMinuteRate;" + \
          "server.delayedfetchrequestmetrics.followerexpirespersecond.count=kafka.server:type=DelayedFetchRequestMetrics,name=FollowerExpiresPerSecond/Count;" + \
          "server.delayedfetchrequestmetrics.followerexpirespersecond.eventtype=kafka.server:type=DelayedFetchRequestMetrics,name=FollowerExpiresPerSecond/EventType;" + \
          "server.delayedfetchrequestmetrics.followerexpirespersecond.rateunit=kafka.server:type=DelayedFetchRequestMetrics,name=FollowerExpiresPerSecond/RateUnit;" + \
          "server.delayedfetchrequestmetrics.followerexpirespersecond.meanrate=kafka.server:type=DelayedFetchRequestMetrics,name=FollowerExpiresPerSecond/MeanRate;" + \
          "server.delayedfetchrequestmetrics.followerexpirespersecond.oneminuterate=kafka.server:type=DelayedFetchRequestMetrics,name=FollowerExpiresPerSecond/OneMinuteRate;" + \
          "server.delayedfetchrequestmetrics.followerexpirespersecond.fiveminuterate=kafka.server:type=DelayedFetchRequestMetrics,name=FollowerExpiresPerSecond/FiveMinuteRate;" + \
          "server.delayedfetchrequestmetrics.followerexpirespersecond.fifteenminuterate=kafka.server:type=DelayedFetchRequestMetrics,name=FollowerExpiresPerSecond/FifteenMinuteRate;" + \
          "server.replicamanager.leadercount.value=kafka.server:type=ReplicaManager,name=LeaderCount/Value;" + \
          "server.brokertopicmetrics.failedfetchrequestspersec.count=kafka.server:type=BrokerTopicMetrics,name=FailedFetchRequestsPerSec/Count;" + \
          "server.brokertopicmetrics.failedfetchrequestspersec.eventtype=kafka.server:type=BrokerTopicMetrics,name=FailedFetchRequestsPerSec/EventType;" + \
          "server.brokertopicmetrics.failedfetchrequestspersec.rateunit=kafka.server:type=BrokerTopicMetrics,name=FailedFetchRequestsPerSec/RateUnit;" + \
          "server.brokertopicmetrics.failedfetchrequestspersec.meanrate=kafka.server:type=BrokerTopicMetrics,name=FailedFetchRequestsPerSec/MeanRate;" + \
          "server.brokertopicmetrics.failedfetchrequestspersec.oneminuterate=kafka.server:type=BrokerTopicMetrics,name=FailedFetchRequestsPerSec/OneMinuteRate;" + \
          "server.brokertopicmetrics.failedfetchrequestspersec.fiveminuterate=kafka.server:type=BrokerTopicMetrics,name=FailedFetchRequestsPerSec/FiveMinuteRate;" + \
          "server.brokertopicmetrics.failedfetchrequestspersec.fifteenminuterate=kafka.server:type=BrokerTopicMetrics,name=FailedFetchRequestsPerSec/FifteenMinuteRate;" + \
          "server.replicamanager.isrshrinkspersec.count=kafka.server:type=ReplicaManager,name=IsrShrinksPerSec/Count;" + \
          "server.replicamanager.isrshrinkspersec.eventtype=kafka.server:type=ReplicaManager,name=IsrShrinksPerSec/EventType;" + \
          "server.replicamanager.isrshrinkspersec.rateunit=kafka.server:type=ReplicaManager,name=IsrShrinksPerSec/RateUnit;" + \
          "server.replicamanager.isrshrinkspersec.meanrate=kafka.server:type=ReplicaManager,name=IsrShrinksPerSec/MeanRate;" + \
          "server.replicamanager.isrshrinkspersec.oneminuterate=kafka.server:type=ReplicaManager,name=IsrShrinksPerSec/OneMinuteRate;" + \
          "server.replicamanager.isrshrinkspersec.fiveminuterate=kafka.server:type=ReplicaManager,name=IsrShrinksPerSec/FiveMinuteRate;" + \
          "server.replicamanager.isrshrinkspersec.fifteenminuterate=kafka.server:type=ReplicaManager,name=IsrShrinksPerSec/FifteenMinuteRate;" + \
          "server.delayedfetchrequestmetrics.consumerexpirespersecond.count=kafka.server:type=DelayedFetchRequestMetrics,name=ConsumerExpiresPerSecond/Count;" + \
          "server.delayedfetchrequestmetrics.consumerexpirespersecond.eventtype=kafka.server:type=DelayedFetchRequestMetrics,name=ConsumerExpiresPerSecond/EventType;" + \
          "server.delayedfetchrequestmetrics.consumerexpirespersecond.rateunit=kafka.server:type=DelayedFetchRequestMetrics,name=ConsumerExpiresPerSecond/RateUnit;" + \
          "server.delayedfetchrequestmetrics.consumerexpirespersecond.meanrate=kafka.server:type=DelayedFetchRequestMetrics,name=ConsumerExpiresPerSecond/MeanRate;" + \
          "server.delayedfetchrequestmetrics.consumerexpirespersecond.oneminuterate=kafka.server:type=DelayedFetchRequestMetrics,name=ConsumerExpiresPerSecond/OneMinuteRate;" + \
          "server.delayedfetchrequestmetrics.consumerexpirespersecond.fiveminuterate=kafka.server:type=DelayedFetchRequestMetrics,name=ConsumerExpiresPerSecond/FiveMinuteRate;" + \
          "server.delayedfetchrequestmetrics.consumerexpirespersecond.fifteenminuterate=kafka.server:type=DelayedFetchRequestMetrics,name=ConsumerExpiresPerSecond/FifteenMinuteRate;" + \
          "network.socketserver.idlepercent.networkprocessor.2.count=kafka.network:type=SocketServer,name=IdlePercent,networkProcessor=2/Count;" + \
          "network.socketserver.idlepercent.networkprocessor.2.eventtype=kafka.network:type=SocketServer,name=IdlePercent,networkProcessor=2/EventType;" + \
          "network.socketserver.idlepercent.networkprocessor.2.rateunit=kafka.network:type=SocketServer,name=IdlePercent,networkProcessor=2/RateUnit;" + \
          "network.socketserver.idlepercent.networkprocessor.2.meanrate=kafka.network:type=SocketServer,name=IdlePercent,networkProcessor=2/MeanRate;" + \
          "network.socketserver.idlepercent.networkprocessor.2.oneminuterate=kafka.network:type=SocketServer,name=IdlePercent,networkProcessor=2/OneMinuteRate;" + \
          "network.socketserver.idlepercent.networkprocessor.2.fiveminuterate=kafka.network:type=SocketServer,name=IdlePercent,networkProcessor=2/FiveMinuteRate;" + \
          "network.socketserver.idlepercent.networkprocessor.2.fifteenminuterate=kafka.network:type=SocketServer,name=IdlePercent,networkProcessor=2/FifteenMinuteRate;" + \
          "network.socketserver.responsesbeingsent.value=kafka.network:type=SocketServer,name=ResponsesBeingSent/Value;" + \
          "network.requestchannel.responsequeuesize.processor.1.value=kafka.network:type=RequestChannel,name=ResponseQueueSize,processor=1/Value;" + \
          "server.replicamanager.isrexpandspersec.count=kafka.server:type=ReplicaManager,name=IsrExpandsPerSec/Count;" + \
          "server.replicamanager.isrexpandspersec.eventtype=kafka.server:type=ReplicaManager,name=IsrExpandsPerSec/EventType;" + \
          "server.replicamanager.isrexpandspersec.rateunit=kafka.server:type=ReplicaManager,name=IsrExpandsPerSec/RateUnit;" + \
          "server.replicamanager.isrexpandspersec.meanrate=kafka.server:type=ReplicaManager,name=IsrExpandsPerSec/MeanRate;" + \
          "server.replicamanager.isrexpandspersec.oneminuterate=kafka.server:type=ReplicaManager,name=IsrExpandsPerSec/OneMinuteRate;" + \
          "server.replicamanager.isrexpandspersec.fiveminuterate=kafka.server:type=ReplicaManager,name=IsrExpandsPerSec/FiveMinuteRate;" + \
          "server.replicamanager.isrexpandspersec.fifteenminuterate=kafka.server:type=ReplicaManager,name=IsrExpandsPerSec/FifteenMinuteRate;"


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