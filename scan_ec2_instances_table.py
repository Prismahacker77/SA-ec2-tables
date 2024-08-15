import boto3
from prettytable import PrettyTable

def get_regions():
    ec2_client = boto3.client('ec2')
    return [region['RegionName'] for region in ec2_client.describe_regions()['Regions']]

def prefetch_route_tables(ec2, vpc_id):
    route_table_targets = {}
    route_tables = ec2.describe_route_tables(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])['RouteTables']
    
    for rt in route_tables:
        for route in rt['Routes']:
            if route.get('DestinationCidrBlock') == '0.0.0.0/0':
                target = 'None'
                if 'GatewayId' in route and route['GatewayId'].startswith('igw-'):
                    target = 'IGW'
                elif 'NatGatewayId' in route:
                    target = 'NATGW'
                elif 'TransitGatewayId' in route:
                    target = 'TGW'
                elif 'VpcPeeringConnectionId' in route:
                    target = 'VpcPeering'
                else:
                    target = route.get('GatewayId', 'Other')
                
                for assoc in rt['Associations']:
                    subnet_id = assoc.get('SubnetId')
                    if subnet_id:
                        route_table_targets[subnet_id] = target
    
    return route_table_targets

def get_instances(ec2):
    return ec2.describe_instances()['Reservations']

def scan_ec2_instances():
    regions = get_regions()
    table = PrettyTable()
    table.field_names = ["Region", "Instance ID", "Public IP", "Subnet ID", "VPC ID", "Availability Zone", "Route Table Target"]

    for region in regions:
        ec2 = boto3.client('ec2', region_name=region)
        instances = get_instances(ec2)

        for reservation in instances:
            for instance in reservation['Instances']:
                instance_id = instance['InstanceId']
                vpc_id = instance.get('VpcId')
                subnet_id = instance.get('SubnetId')
                public_ip = instance.get('PublicIpAddress')
                az = instance.get('Placement', {}).get('AvailabilityZone', 'N/A')

                # Prefetch route table targets for the VPC
                route_table_targets = prefetch_route_tables(ec2, vpc_id)
                route_table_target = route_table_targets.get(subnet_id, 'None')

                # Ensure correct output
                table.add_row([region, instance_id, public_ip, subnet_id, vpc_id, az, route_table_target])

    print(table)

if __name__ == "__main__":
    scan_ec2_instances()