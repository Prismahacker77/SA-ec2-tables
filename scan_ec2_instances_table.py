import boto3
from prettytable import PrettyTable

def get_regions():
    ec2_client = boto3.client('ec2')
    return [region['RegionName'] for region in ec2_client.describe_regions()['Regions']]

def get_route_table_targets(ec2, vpc_id):
    route_tables = ec2.describe_route_tables(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])['RouteTables']
    subnet_to_target = {}

    for rt in route_tables:
        for route in rt['Routes']:
            if route.get('DestinationCidrBlock') == '0.0.0.0/0':
                target = route.get('GatewayId') or route.get('NatGatewayId') or route.get('TransitGatewayId') or route.get('VpcPeeringConnectionId') or 'None'
                target_name = 'None'
                if target.startswith('igw-'):
                    target_name = 'IGW'
                elif target.startswith('nat-'):
                    target_name = 'NATGW'
                
                for assoc in rt['Associations']:
                    if assoc.get('SubnetId'):
                        subnet_to_target[assoc['SubnetId']] = target_name

    return subnet_to_target

def get_instances(ec2, region):
    return ec2.describe_instances()['Reservations']

def scan_ec2_instances():
    regions = get_regions()
    table = PrettyTable()
    table.field_names = ["Region", "Instance ID", "Public IP", "Subnet ID", "VPC ID", "Availability Zone", "Route Table Target", "Internet Accessible"]

    for region in regions:
        ec2 = boto3.client('ec2', region_name=region)
        instances = get_instances(ec2, region)

        for reservation in instances:
            for instance in reservation['Instances']:
                instance_id = instance['InstanceId']
                vpc_id = instance.get('VpcId')
                subnet_id = instance.get('SubnetId')
                public_ip = instance.get('PublicIpAddress')
                az = instance.get('Placement', {}).get('AvailabilityZone', 'N/A')

                # Get the route table targets for the VPC
                route_table_targets = get_route_table_targets(ec2, vpc_id)
                route_table_target = route_table_targets.get(subnet_id, 'None')
                internet_accessible = 'Yes' if route_table_target == 'IGW' else 'No'

                table.add_row([region, instance_id, public_ip, subnet_id, vpc_id, az, route_table_target, internet_accessible])

    print(table)

if __name__ == "__main__":
    scan_ec2_instances()