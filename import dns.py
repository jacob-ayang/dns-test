import dns.resolver
import time
import threading
import logging
import random

# 配置日志记录，同时输出到终端和文件
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# 创建文件处理器，将日志写入文件
file_handler = logging.FileHandler('D:\\dev\\dns_stress_test_log.txt')
file_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))

# 获取根日志记录器并添加文件处理器
logger = logging.getLogger()
logger.addHandler(file_handler)

# 指定DNS服务器地址
DNS_SERVER = "8.8.8.8"

# 线程安全的计数器和锁
success_count = 0
failure_count = 0
counter_lock = threading.Lock()

# 加载域名列表
def load_domains(file_path):
    try:
        with open(file_path, 'r') as f:
            domains = [line.strip() for line in f if line.strip()]
        if not domains:
            raise ValueError("域名列表为空，请检查文件内容。")
        return domains
    except Exception as e:
        logger.error(f"加载域名列表失败: {e}")
        return []

# 查询DNS
def query_dns(domain):
    global success_count, failure_count
    resolver = dns.resolver.Resolver()
    resolver.nameservers = [DNS_SERVER]
    resolver.timeout = 5  # 调整超时时间
    resolver.lifetime = 10  # 总超时时间

    try:
        start_time = time.time()
        result = resolver.resolve(domain, 'A')  # 可尝试改为 'CNAME' 或 'AAAA'
        ips = [ipval.to_text() for ipval in result]
        elapsed = time.time() - start_time
        with counter_lock:
            success_count += 1
        logger.info(f"Success: Domain: {domain}, Resolved IPs: {ips} (Time: {elapsed:.2f}s)")
    except Exception as e:
        with counter_lock:
            failure_count += 1
        logger.error(f"Failure: Domain: {domain}, Error: {str(e)} | DNS Server: {DNS_SERVER}")

# 压测函数
def stress_test(duration_seconds, domains):
    global success_count, failure_count
    start_time = time.time()
    threads = []
    success_count = 0
    failure_count = 0

    logger.info(f"Started stress test (Duration: {duration_seconds}s | Target DNS: {DNS_SERVER})")

    # 创建线程并控制频率
    while time.time() - start_time < duration_seconds:
        domain = random.choice(domains)  # 随机选择一个域名
        thread = threading.Thread(target=query_dns, args=(domain,))
        threads.append(thread)
        thread.start()
        time.sleep(0.01)  # 调整为0.01秒，减少线程创建频率

    # 等待所有线程完成
    for thread in threads:
        thread.join()

    end_time = time.time()
    total_queries = success_count + failure_count
    success_rate = (success_count / total_queries * 100) if total_queries > 0 else 0

    logger.info(f"Test completed in {end_time - start_time:.2f}s. "
                f"Success: {success_count}, Failed: {failure_count}, "
                f"Total: {total_queries}, Success Rate: {success_rate:.2f}%")

if __name__ == "__main__":
    # 加载域名列表
    domain_list = load_domains('D:\\dev\\domains.txt')
    if domain_list:
        stress_test(100, domain_list)  # 默认测试100秒