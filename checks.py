def is_owner_check(message):
    return message.author.id == '112311949416488960'


def check_permissions(ctx, **perms):
    msg = ctx.message
    if is_owner_check(msg):
        return True

    ch = msg.channel
    author = msg.author
    resolved = ch.permissions_for(author)
    return all(getattr(resolved, name, None) == value for name, value in perms.items())



