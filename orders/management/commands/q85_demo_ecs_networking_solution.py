from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q85 SOLUTION: Minimal security groups using SG references.
    ECS ingress only from ALB. RDS ingress only from ECS SG.
    Egress restricted to required ports only.
    """
    help = 'Q85 Solution: Least-privilege security group configuration'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q85 SOLUTION: Least-privilege ECS networking')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        Order.objects.create(
            order_number='Q85-SOL-ORDER',
            customer_email='q85sol@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )

        # Correct security group configuration
        security_groups = {
            'alb-sg': {
                'ingress': [('0.0.0.0/0', 80, 'HTTPS from internet'), ('0.0.0.0/0', 443, 'HTTPS from internet')],
                'egress': [('ecs-tasks-sg', 8000, 'to ECS only')],
            },
            'ecs-tasks-sg': {
                'ingress': [('alb-sg', 8000, 'from ALB only — NOT internet')],
                'egress': [
                    ('rds-sg', 5432, 'to RDS'),
                    ('0.0.0.0/0', 6379, 'to Redis/ElastiCache'),
                    ('0.0.0.0/0', 443, 'to AWS APIs (S3, SQS, etc.)'),
                ],
            },
            'rds-sg': {
                'ingress': [('ecs-tasks-sg', 5432, 'from ECS tasks only')],
                'egress': [],
            },
        }

        self.stdout.write('Security group configuration:')
        for sg_name, rules in security_groups.items():
            self.stdout.write(f'\n  {sg_name}:')
            if rules['ingress']:
                self.stdout.write('    Ingress:')
                for source, port, note in rules['ingress']:
                    self.stdout.write(self.style.SUCCESS(f'      {source} port {port} ({note})'))
            if rules['egress']:
                self.stdout.write('    Egress:')
                for dest, port, note in rules['egress']:
                    self.stdout.write(f'      {dest} port {port} ({note})')

        self.stdout.write('\nValidation: ECS -> RDS connectivity:')
        # Simulate reachability check
        ecs_sg_has_rds_rule = any(
            dest == 'rds-sg' and port == 5432
            for dest, port, _ in security_groups['ecs-tasks-sg']['egress']
        )
        rds_sg_allows_ecs = any(
            source == 'ecs-tasks-sg' and port == 5432
            for source, port, _ in security_groups['rds-sg']['ingress']
        )
        reachable = ecs_sg_has_rds_rule and rds_sg_allows_ecs
        if reachable:
            self.stdout.write(self.style.SUCCESS('  ECS -> RDS: REACHABLE OK'))
        else:
            self.stdout.write(self.style.ERROR('  ECS -> RDS: BLOCKED ✗'))

        self.stdout.write('\nVPC Reachability Analyzer:')
        self.stdout.write('  Source: ECS task network interface')
        self.stdout.write('  Destination: RDS instance port 5432')
        self.stdout.write('  Run BEFORE every deploy — catches misconfigs early')

        self.stdout.write('\nTerraform / CDK example (SG reference pattern):')
        self.stdout.write('  rds_sg.add_ingress_rule(')
        self.stdout.write('      peer=ecs_sg,            # SG reference, not CIDR')
        self.stdout.write('      connection=ec2.Port.tcp(5432)')
        self.stdout.write('  )')

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - ECS ingress ONLY from ALB security group')
        self.stdout.write('  - RDS ingress ONLY from ECS security group')
        self.stdout.write('  - Use SG references (not CIDR ranges) — dynamic, correct')
        self.stdout.write('  - Use VPC Reachability Analyzer to validate before deploy')
