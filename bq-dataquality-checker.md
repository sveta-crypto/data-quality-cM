# Solution Design Document - Explanation

## Topic Name / Project Name
| Version Number | Date    | Author(s) | Changes |
|----------------|---------|-----------|---------|
|               1| 26/9/24 | Sveta     |         |

## Table of Contents
- [Introduction](#introduction)
- [System Overview](#system-overview)
- [Requirements](#requirements)
- [Solution Design](#solution-design)
- [Integration](#integration)
- [Security / Privacy (GDPR)](#security--privacy-gdpr)
- [Performance and Scalability](#performance-and-scalability)
- [Testing and Quality Assurance](#testing-and-quality-assurance)
- [Deployment and Maintenance](#deployment-and-maintenance)
- [Expected Costs](#expected-costs)
- [Appendices](#appendices)
- [Usefull links](#usefull-links)

## Introduction
### Purpose of the Document: 
The purpose of this SSD is to identify data quality issues within the CitizenM events data, containing app user data, export in BigQuery. 
### Project Overview: 
The app events data from firebase is exported in to BigQuery, which consists of data for analysis purposes. The quality of this data needs to satisfy a certain criteria. This criteria consists of the folowing: 
* The naming for events or screens need to be consistent with the naming convention that has been documented
* The naming for events or screens need to be consistent between platforms
* Certain event names are GA4 key events and need to be present in the data

In reality these criteria are not always met, which leads to low data quality. This further leads to unreliable data and data anlysis because of missing periods of data or missing data for a certain platform. Also a significant amount of time is spent to work around these problems in order to restore the data. To fix this problem the quality of the data needs to be monitored based on the aforementioned criteria.  
To achieve this a function will be used. This function will do tests on this dataset like; testing for an odd ammount of rows, wrongfully named events and missing events. The results of these tests will be saved as reports. thresholds will be used to check the quality. If certain report numbers are off, this will be alerted through an email or a message to slack. 
### Audience: 
data analyst ONBRDNG, Data team citizenM, PO App team & web team 

## System Overview: 
### System Context: 
python will be used to make a function, this function queries the dataset from BQ so the data is aggregated by events with a count of the number of instances per event. The function uses a whitelist containing events that need to be present. These aggregated query results are saved within a new dataset in BQ. The results in the dataset are used to test whether there are counts equal to zero or of the counts are within the threshold. If there are abnormalities alerts are send using sendgrid API. This function will be deployed into the google cloud environment of cM where the process will be executed once every day.
### Key Stakeholders

| Stakeholder | Department  | Role          |
|-------------|-------------|---------------|
| Arno        | cM app team | Data analyst  |
| Can         | ONBRDNG     | Data scientist| 
| Kevin       | cM app team | App developer |
| Wien        | cM app team | App developer |
| Esmée       | cM app team | Product owner |
| Marvin      | ONBRDNG     | CTO           |
| Dennis      | cM web team | Poduct owner  |

## Requirements
### Functional Requirements:
* Alerting via slack
* Report saved in BQ table
* check dq on date before today
* key events check
  
### Non-Functional Requirements:
Performance doens not need to be scalable, sinds dataset does not grow daily

## Solution Design
### High-Level Architecture Diagram: 

<img width="900" alt="image" src="https://github.com/user-attachments/assets/16710fa6-c7da-4ad8-a9e7-6c42ceb225c8">

### System Components:
* Scheduler: For daily invocation function in Google Cloud Functions. 
* Checker: Function that queries data from BQ to be checked. The function checks wether certain events are present and compliant with naming convention. If these are not correct alerting will be send. 
* Google Cloud Functions: Main environment in which the scheduler, checker and data are available and working. 
* Slack API: API to use to send alerting message 
### Data Flow & Sequence Diagrams: 

<img width="664" alt="image" src="https://github.com/user-attachments/assets/a461f556-e614-47ad-9948-7edd8902d2ee">



[The text used to create above sequence diagram](https://www.websequencediagrams.com/?lz=dGl0bGUgZGF0YSBxdWFsaXR5IGNoZWNrZXIKCnBhcnRpY2lwYW50IHNjaGVkdWxlciAACg0AJQcABw5CUQAuDVNsYWNrIEFQSQphY3RvciBjTQoKAEYJLT4AaAc6IGludm9rZSBmdW5jdGlvbgoKbG9vcCBmb3IgZXZlcnkgRFEgcXVlcnkKAIEaBy0-K0JROiBwZXJmb3JtAIE2DgAjBkJRLT4tAFcJcmV0dXJuIHJlc3VsdCAAPApCUTogQWRkIERRIHJlcG9ydAoKCmVuZApvcHQgd2hlbiBEUSBpc3N1ZQBuCwCBSwk6IHRyaWdnZXIgQVBJIHRvIHNlbmQgYWxlcnRzCgCBcQktLT4tY006IFMAFAkAXQUK&s=modern-blue)

### [Optional] Class/Entity Diagrams
### [Optional] API Design

## Integration
### External Interfaces
### Integration Patterns

## Security / Privacy (GDPR)
### Security Requirements
### Authentication and Authorization
### Data Encryption
### Vulnerability Management
### Sensitive data & Privacy

## Performance and Scalability
### Performance Requirements
### Scalability Plan

## Testing and Quality Assurance
### Test Plan
### Test Cases
### QA Processes

## Deployment and Maintenance
### Deployment Plan
### Maintenance Plan
### Logging, Monitoring & Alerting

## Expected Costs
### Development Costs
### Infrastructure Costs
### Software Licenses
### Maintenance and Support Costs
### Other Costs

## Appendices
### Glossary
### References
