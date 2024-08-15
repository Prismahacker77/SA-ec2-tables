import boto3
from prettytable import PrettyTable

def get_regions():
    ec2_client = boto3.client('ec2')
    return [region['RegionName'] for region in ec2_client.describe_regions()['Regions']]

def get_instances(ec2, region):
    return ec2.describe_instances()['Reservations']

def scan_ec2_instances():
    regions = get_regions()
    table = PrettyTable()
    table.field_names = ["Region", "Instance ID", "Public IP", "Subnet ID", "VPC ID", "Availability Zone"]

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

                table.add_row([region, instance_id, public_ip, subnet_id, vpc_id, az])

    print(table)

if __name__ == "__main__":
    scan_ec2_instances()