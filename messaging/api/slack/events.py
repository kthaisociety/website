from user.models import User
from event.models import Event
from event.enums import RegistrationStatus, Registration

def join_event(user_id : str, event_ts: str):
    event = Event.objects.published().filter(slack_ts=event_ts).first()
    if not event:
        # User has reacted to a message with the emoji, but it is not an event
        # announcement
        #TODO Should a message be sent?
        return

    user = User.objects.filter(slack_id=user_id).first()
    if not user:
        # User hasn't linked their slack account with their kthais account
        #TODO Should a message be sent?
        return
    
    registration = Registration.objects.filter(event=event, user=user).first()
    if registration:
        # User has already registered to the event.
        #TODO Should a message be sent?
        return
    
    if not event.registration_available or not event.is_signup_open: 
        # Cannot register now
        #TODO Should a message be sent?
        return

    if event.has_food and not (user.diet or user.diet_other) :
        # The event has food, but it is not collected from slack now
        #TODO Should a message be sent?
        return

    if event.collect_resume and not user.resume:
        #The event requires a resume and the user has not upload one in kthais.com
        #TODO Should a message be sent?
        return

    registration = Registration.objects.create(
                        event = event,
                        user = user,
                        status = RegistrationStatus.REGISTERED,
                        diet = user.diet,
                        diet_other = user.diet_other,
                    )
    if registration:
        #TODO Should a message be sent?
        send_registration_email(registration_id=registration.id)


def leave_event(user_id : str, event_ts: str):
    event = Event.objects.published().filter(slack_ts=event_ts).first()
    if not event:
        # User has reacted to a message with the emoji, but it is not an event
        # announcement
        #TODO Should a message be sent?
        return

    user = User.objects.filter(slack_id=user_id).first()
    if not user:
        # User hasn't linked their slack account with their kthais account
        #TODO Should a message be sent?
        return
    
    registration = Registration.objects.filter(event=event, user=user).first()
    if not registration:
        # User is not registered to the event.
        #TODO Should a message be sent?
        return
    
    registration.status = RegistrationStatus.CANCELLED
    registration.save()
    
    if registration:
        #TODO Should a message be sent?
        send_registration_email(registration_id=registration.id)

