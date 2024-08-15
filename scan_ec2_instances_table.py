import boto3
from prettytable import PrettyTable

def get_regions():
    ec2_client = boto3.client('ec2')
    return [region['RegionName'] for region in ec2_client.describe_regions()['Regions']]

def get_route_table_target_and_accessibility(ec2, subnet_id):
    # Describe route tables to find the one associated with the subnet
    route_tables = ec2.describe_route_tables(Filters=[{'Name': 'association.subnet-id', 'Values': [subnet_id]}])['RouteTables']
    
    for rt in route_tables:
        for route in rt['Routes']:
            if route.get('DestinationCidrBlock') == '0.0.0.0/0':
                target = route.get('GatewayId') or route.get('NatGatewayId') or route.get('TransitGatewayId') or route.get('VpcPeeringConnectionId') or 'None'
                if target.startswith('igw-'):
                    return target, "Yes"
                else:
                    return target, "No"
    return 'None', 'No'

def get_instances(ec2, region):
    return ec2.describe_instances()['Reservations']

def scan_ec2_instances():
    regions = get_regions()
    table = PrettyTable()
    table.field_names = ["Region", "EC2 Count", "Instance ID", "Internet Accessible", "Public IP", "Subnet ID", "Route Table Target", "VPC ID", "Availability Zone"]

    for region in regions:
        ec2 = boto3.client('ec2', region_name=region)
        instances = get_instances(ec2, region)
        ec2_count = sum(len(reservation['Instances']) for reservation in instances)

        for reservation in instances:
            for instance in reservation['Instances']:
                instance_id = instance['InstanceId']
                vpc_id = instance.get('VpcId')
                subnet_id = instance.get('SubnetId')
                public_ip = instance.get('PublicIpAddress')
                az = instance.get('Placement', {}).get('AvailabilityZone', 'N/A')
                route_table_target, internet_accessible = get_route_table_target_and_accessibility(ec2, subnet_id)

                table.add_row([region, ec2_count, instance_id, internet_accessible, public_ip, subnet_id, route_table_target, vpc_id, az])

    print(table)

if __name__ == "__main__":
    scan_ec2_instances()