#!/usr/bin python3
import sys, os, subprocess, argparse

if __name__ == "__main__":
    try:
        import pygame
    except:
        try:
            import pip
        except:
            sys.exit("Could not import pip package manager. Please install pip for your python distribution.")

        subprocess.check_call(["python3", '-m', 'pip', 'install', 'pygame']) # install pkg
        subprocess.check_call(["python3", '-m', 'pip', 'install',"--upgrade", 'pygame']) # upgrade pkg
        subprocess.check_call(["python3", '-m', 'pip', 'install', 'netifaces']) # install netifaces package

    sys.path.insert(0, "%s/core/" % os.path.dirname(os.path.realpath(__file__)))
    sys.path.insert(0, "%s/bomberman_src/" % os.path.dirname(os.path.realpath(__file__)))

    argparser = argparse.ArgumentParser(description="An online gridcoloring adventure written in Python.")

    argparser.add_argument("--username", dest="username", help="Username", required=True )
    argparser.add_argument("--client_port", dest="port",type=int,  help="Client port", required=True)
    argparser.add_argument("--serv_ip", dest="server_ip", help="Server ip address.", required=True)
    argparser.add_argument("--serv_port", dest="server_port", type=int, help="Server port", required=True)
    argparser.add_argument("--is_server", dest="is_server", action="store_true", default=False, help="Make the player a server")
    args = argparser.parse_args()

    import bomberman_main

    bomberman_main.main(args.username, args.port, args.server_ip, args.server_port, args.is_server)

"""
    try:
        bomberman_main.main(args.username, args.port, args.server_ip, args.server_port, args.is_server)
    except Exception as e:
        sys.exit("Game crashed with error: %s" % e)
"""