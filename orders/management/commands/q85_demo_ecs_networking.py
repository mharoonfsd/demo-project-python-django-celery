from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q85 PROBLEM: ECS task security group too permissive (0.0.0.0/0 ingress)
    OR missing RDS security group rule. In the first case, any internet traffic
    reaches the container. In the second, ECS tasks cannot connect to RDS
    and get cryptic connection refused errors.
    """
    help = 'Q85 Problem: ECS networking misconfiguration - security group errors'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q85 PROBLEM: ECS networking - security group misconfiguration')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        Order.objects.create(
            order_number='Q85-ORDER',
            customer_email='q85@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )

        # Scenario 1: Too permissive - direct internet access to ECS
        self.stdout.write('Scenario A: ECS task security group too permissive')
        self.stdout.write('  SG ecs-tasks-sg:')
        self.stdout.write('    Ingress: 0.0.0.0/0 port 8000  <- WRONG: allows internet direct access')
        self.stdout.write('    Egress:  all')
        self.stdout.write(self.style.ERROR(
            '  PROBLEM: Direct internet access bypasses ALB WAF rules'
            '\n  Attacker can reach ECS directly without WAF protection'
        ))

        # Scenario B: Missing rule between ECS and RDS
        self.stdout.write('\nScenario B: ECS cannot reach RDS - missing inbound rule')
        self.stdout.write('  SG rds-sg (RDS security group):')
        self.stdout.write('    Ingress: sg-bastion port 5432  <- Only bastion allowed')
        self.stdout.write('    (MISSING: ecs-tasks-sg inbound rule)')
        self.stdout.write(self.style.ERROR(
            '  ECS tasks try: psycopg2.connect(host=rds.xxx.rds.amazonaws.com)'
            '\n  ERROR: connection to server ... failed: Connection refused'
            '\n  Cryptic: looks like wrong host or wrong port'
            '\n  Root cause: security group missing ECS->RDS ingress rule'
        ))

        self.stdout.write(self.style.ERROR(
            '\nPROBLEM: Both scenarios are common and hard to debug'
            '\n  - Scenario A: security hole not visible until audit'
            '\n  - Scenario B: ops wastes hours checking DB credentials'
            '\n    before realizing it is a network rule issue'
        ))

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - ECS tasks: ingress ONLY from ALB security group')
        self.stdout.write('  - RDS: ingress from ECS-SG on port 5432/3306 ONLY')
        self.stdout.write('  - Test with VPC Reachability Analyzer before deploy')
        self.stdout.write('  - Use security group references (not CIDR ranges)')
