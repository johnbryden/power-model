from pylab import *
from collections import namedtuple
import sys

# Right I want a list of nodes and undirectional connections

class Link:

    def __init__(self, outPerson, inPerson, linkValueToOut, linkValueToIn):
        self.outPerson = outPerson
        self.inPerson = inPerson
        self.linkValueToOut = linkValueToOut
        self.linkValueToIn = linkValueToIn

class Person:
    
    def __init__ (self,personid):

        # this the id of the person
        self.personid = personid

        # the person has a list of its Links to other people
        self.outgoingLinks=list()
        # they also have a list of Links from others
        self.incomingLinks=dict()

        # this is the initial status of the person
        self.status=1.0
        # this is the incoming status
        self.incomingStatus = 0

    def show (self):
        print "I am person",self.personid
        print "I have status",self.status
        print "Incoming status is",self.incomingStatus
        for link in self.outgoingLinks:
            print "->",link.inPerson.personid
        print len(self.incomingLinks),"incoming links"
        print

    def getNumLinks(self):
        return len(self.incomingLinks)+len(self.outgoingLinks)
        
    def updateStatus(self):
        status += statusChange
        statusChange = 0

    def getWorstLink(self):
        worstlink = None
        worstValue= 1e500
        for link in self.outgoingLinks:
            if link.linkValueToOut < worstValue:
                worstValue = link.linkValueToOut
                worstlink = link

        return worstlink

#    def addOutgoingLink(self,linkedPerson):
#        outgoingLinks.append(Link(linkedPerson=linkedPerson,linkValue=0.0))

#    def addIncomingLink(self,linkedPerson):
#        outgoingLinks.append(Link(linkedPerson=linkedPerson,linkValue=0.0))
        


# How does link value work?

# The whole things starts with numpeople status 'points' at the
# beginning.  That should be conserved.
#
# In total there are numpeople*numLinks*2 actual Links

# The link's status is person1Status/person1TotalLinks +
# person2/person2TotalLinks

# With an inequality factor of q, the person with the link incoming
# gets q of the shared status.


class Population:
    # a dictionary from id to Person
    
    numPeople = 20
    numLinks  = 5
    
    # this is essentially a C struct

    def __init__(self):

        self.q = 0.9
        self.r = 0.2
        self.w = 1.0

        self.people = dict()
        self.links = list()

        #        self.numlinksvsstatus_output=open('numlinksvsstatus.dat','w')
        self.numlinksvsstatus=list()

        for i in range (0,self.numPeople):
            self.people[i] = Person(i)

        for pid,person in self.people.items():
            avoidPeople=[person.personid,]
            for j in range (0,self.numLinks):
                linkedPerson=self.findIndividualToLinkTo(avoidPeople)
                avoidPeople.append(linkedPerson.personid)
                newlink = Link(outPerson = person, inPerson = linkedPerson, linkValueToOut = 0.0, linkValueToIn = 0.0)
                self.links.append (newlink)
                person.outgoingLinks.append(newlink)
                linkedPerson.incomingLinks[person.personid]=newlink


    def getRandomPerson (self):
        return self.people[randint(self.numPeople)]
                
    def findIndividualToLinkTo (self, avoidPeopleIDs):
        newPerson = self.getRandomPerson()
        while newPerson.personid in avoidPeopleIDs:
            newPerson = self.getRandomPerson()

        return newPerson
        
        

    def showPeople(self):
        for pid,person in self.people.items():
            person.show()

    def updateStatuses(self):
        for link in self.links:
            link.linkValueToIn = 0.0
            link.linkValueToOut = 0.0
        
        for link in self.links:
            outPerson = link.outPerson
            inPerson = link.inPerson

            # Each person gives a proportion r of their status and
            # divides that amongst their links.
            outStatusForLink = self.r*outPerson.status/float(outPerson.getNumLinks())
            inStatusForLInk = self.r*inPerson.status/float(inPerson.getNumLinks())
         
            # The status attributed to each link is divided unevenly
            # between the pair - with a proportion q going to the
            # person who's getting their link
            linkValue = outStatusForLink+inStatusForLInk
            link.linkValueToIn = linkValue*self.q
            link.linkValueToOut = linkValue*(1.0-self.q)

            outPerson.incomingStatus += link.linkValueToOut
            inPerson.incomingStatus += link.linkValueToIn

        for pid,person in self.people.items():
            person.status += person.incomingStatus-self.r*person.status
            person.incomingStatus = 0
            
    def outputLinksVersusStatus (self):
        # I want to generate a heat map of status / num links
        for pid,person in self.people.items():
            numlinks = person.getNumLinks()
            status = person.status
            self.numlinksvsstatus.append((numlinks,status))

#            self.numlinksvsstatus_output.write(str(numlinks)+' '+str(status)+'\n')
    
    def getStatuses (self):
        statuses = []
        for pid,person in self.people.items():
            statuses.append(person.status)
        return statuses

    def rewireLinks (self):

        for pid,person in self.people.items():
            if rand() < self.w:
#                print "Person",person.personid,"rewiring from",
                worstLink = person.getWorstLink()
                oldPerson = worstLink.inPerson
                oldPerson.incomingLinks.pop(person.personid)
                #                print oldPerson.personid,

                avoidPeople = [person.personid,]
                for link in person.outgoingLinks:
                    avoidPeople.append(link.inPerson.personid)

                newPerson = self.findIndividualToLinkTo(avoidPeople)

                worstLink.inPerson = newPerson
                newPerson.incomingLinks[person.personid]=worstLink
                if len(newPerson.incomingLinks) == self.numPeople:
                    print person.personid
                    print avoidPeople
                    print newPerson.personid
                    print oldPerson.personid
                    print worstLink.outPerson.personid, worstLink.inPerson.personid
#               print "to",newPerson.personid

    def findAnomalousIndividual (self):
        for pid,person in self.people.items():
            if person.getNumLinks() > (self.numLinks+self.numPeople-1):
                print "Person: ",person.personid
                for link in self.links:
                    if link.outPerson == person or link.inPerson == person:
                        print link.outPerson.personid,"->",link.inPerson.personid

                        



print sys.argv

qval = 0.9

if len(sys.argv)>1:
    qval = float(sys.argv[1])


print "q = ",qval
 
data=[]
           
population = Population()
population.q = qval
for t in range(0,100000):
    population.updateStatuses()
    population.rewireLinks()
    population.outputLinksVersusStatus()
    population.findAnomalousIndividual()
    statuses=population.getStatuses()
    data.append(statuses)
    
adata=array(data)
figure(1,figsize=(20,10))
subplot (1,2,1)
hold(False)
plot (adata,alpha=0.5)
xlabel('time')
ylabel('status')
subplot (1,2,2)
hold(False)
lvs=array(population.numlinksvsstatus)
plot (lvs[:,0],lvs[:,1],'o',alpha=0.01, markersize=30)
xlabel('Number of links')
ylabel('Status')
savefig(str(qval)+'_fig.png')
#show()



