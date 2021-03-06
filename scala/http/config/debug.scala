// coding:utf-8
// Copyright (C) dirlt

import com.twitter.logging.config._
import org.apache.log4j.{Level => Log4jLevel}
import com.twitter.ostrich.admin.config.{TimeSeriesCollectorConfig, StatsConfig, AdminServiceConfig}
import com.dirlt.scala.finagle.http.HttpConfig

new com.dirlt.scala.finagle.http.HttpConfig {
  serverPort = 8000

  log4jLevel = Log4jLevel.DEBUG

  admin = new AdminServiceConfig {
    httpPort = 8888
    statsNodes = new StatsConfig {
      reporters = new TimeSeriesCollectorConfig
    }
  }

  loggers = new LoggerConfig {
    level = Level.DEBUG
    handlers = new ConsoleHandlerConfig ::
      new FileHandlerConfig {
	filename = "./log/http.debug.log"
        roll = Policy.Daily
      } :: Nil
  }
}
